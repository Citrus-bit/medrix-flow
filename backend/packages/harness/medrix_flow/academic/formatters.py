from __future__ import annotations

import re

from .types import PaperRecord, ReferenceEntry
from .utils import author_display_list, doi_url, normalize_whitespace, slugify


def _sentence_case(title: str) -> str:
    text = normalize_whitespace(title)
    if not text:
        return ""
    return text[0].upper() + text[1:]


def format_apa7_reference(paper: PaperRecord) -> ReferenceEntry:
    authors = author_display_list(paper.authors)
    completeness = "complete"

    if authors:
        if len(authors) <= 20:
            if len(authors) == 1:
                author_part = authors[0]
            else:
                author_part = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            author_part = ", ".join(authors[:19]) + ", ... " + authors[-1]
    else:
        author_part = _sentence_case(paper.title)
        completeness = "missing-author"

    year_text = str(paper.year) if paper.year is not None else "n.d."
    if paper.year is None and completeness == "complete":
        completeness = "missing-year"

    title_text = _sentence_case(paper.title)
    venue_text = normalize_whitespace(paper.venue)
    doi_link = doi_url(paper.doi)
    url = doi_link or paper.oa_url or paper.source_url

    if authors:
        parts = [f"{author_part} ({year_text}). {title_text}."]
    else:
        parts = [f"{author_part} ({year_text})."]

    if venue_text:
        parts.append(f"{venue_text}.")
    elif completeness == "complete":
        completeness = "missing-venue"

    if paper.is_preprint and not venue_text:
        parts.append("arXiv.")

    if url:
        parts.append(url)
    elif completeness == "complete":
        completeness = "incomplete"

    formatted = " ".join(part.strip() for part in parts if part.strip())
    included = (
        completeness in {"complete", "missing-venue", "missing-year", "missing-author"}
        and bool(paper.provider and paper.canonical_source)
    )
    return ReferenceEntry(
        paper_id=paper.paper_id,
        style="apa7",
        formatted_text=re.sub(r"\s+", " ", formatted).strip(),
        doi_url=doi_link,
        completeness=completeness,
        included_in_final=included,
    )


def _bibtex_type(paper: PaperRecord) -> str:
    venue = (paper.venue or "").lower()
    if paper.is_preprint:
        return "misc"
    if "conference" in venue or "proceedings" in venue or "workshop" in venue:
        return "inproceedings"
    return "article"


def _bibtex_escape(value: str) -> str:
    return re.sub(r"([{}])", r"\\\1", value)


def format_bibtex_entry(paper: PaperRecord) -> str:
    author_names = []
    for author in sorted(paper.authors, key=lambda item: item.ordinal):
        if author.family_name and author.given_name:
            author_names.append(f"{author.family_name}, {author.given_name}")
        elif author.display_name:
            author_names.append(author.display_name)

    lead_author = paper.authors[0].family_name if paper.authors and paper.authors[0].family_name else "paper"
    key = f"{slugify(lead_author)}{paper.year or 'nd'}{slugify((paper.title or 'ref').split(' ')[0])}"

    fields: list[tuple[str, str]] = [
        ("title", paper.title),
    ]
    if author_names:
        fields.append(("author", " and ".join(author_names)))
    if paper.year is not None:
        fields.append(("year", str(paper.year)))
    if paper.venue:
        fields.append(("journal" if _bibtex_type(paper) == "article" else "booktitle", paper.venue))
    if paper.doi:
        fields.append(("doi", paper.doi))
    if url := (doi_url(paper.doi) or paper.oa_url or paper.source_url):
        fields.append(("url", url))
    if paper.abstract:
        fields.append(("abstract", paper.abstract))

    rendered_fields = ",\n".join(f"  {name} = {{{_bibtex_escape(value)}}}" for name, value in fields if value)
    return f"@{_bibtex_type(paper)}{{{key},\n{rendered_fields}\n}}"

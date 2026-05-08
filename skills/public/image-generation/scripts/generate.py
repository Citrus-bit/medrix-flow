import base64
import json
import mimetypes
import os
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

DEFAULT_IMAGE_MODEL = "gemini-3-pro-image-preview"
DEFAULT_DRAFT_MODEL = "gemini-2.5-flash-image"
DEFAULT_IMAGE_SIZE = "2K"
SCIENTIFIC_IMAGE_SIZE = "4K"
DEFAULT_OUTPUT_MIME_TYPE = "image/jpeg"
SCIENTIFIC_OUTPUT_MIME_TYPE = "image/png"
SUPPORTED_IMAGE_SIZES = {"1K", "2K", "4K"}
SUPPORTED_OUTPUT_MIME_TYPES = {"image/jpeg", "image/png"}
SCIENTIFIC_GUARDRAIL = (
    "This is a scientific illustration request, not a quantitative data figure. "
    "Do not fabricate plots, axes, p-values, ROC curves, heatmaps, volcano plots, or other measured results. "
    "Generate only a conceptual, explanatory, or graphical-abstract style image consistent with scientific communication."
)


def validate_image(image_path: str) -> bool:
    """
    Validate if an image file can be opened and is not corrupted.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if the image is valid and can be opened, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify that it's a valid image
        # Re-open to check if it can be fully loaded (verify() may not catch all issues)
        with Image.open(image_path) as img:
            img.load()  # Force load the image data
        return True
    except Exception as e:
        print(f"Warning: Image '{image_path}' is invalid or corrupted: {e}")
        return False


def resolve_google_ai_studio_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def resolve_output_mime_type(output_file: str, requested_mime_type: str | None, scientific_mode: bool) -> str:
    if requested_mime_type:
        if requested_mime_type not in SUPPORTED_OUTPUT_MIME_TYPES:
            raise ValueError(f"Unsupported output_mime_type: {requested_mime_type}")
        return requested_mime_type
    if scientific_mode:
        return SCIENTIFIC_OUTPUT_MIME_TYPE
    guessed, _ = mimetypes.guess_type(output_file)
    if guessed in SUPPORTED_OUTPUT_MIME_TYPES:
        return guessed
    return DEFAULT_OUTPUT_MIME_TYPE


def resolve_image_size(requested_image_size: str | None, scientific_mode: bool) -> str:
    image_size = requested_image_size or (SCIENTIFIC_IMAGE_SIZE if scientific_mode else DEFAULT_IMAGE_SIZE)
    if image_size not in SUPPORTED_IMAGE_SIZES:
        raise ValueError(f"Unsupported image_size: {image_size}")
    return image_size


def resolve_model_name(model: str | None, draft_mode: bool = False) -> str:
    if model:
        return model
    return DEFAULT_DRAFT_MODEL if draft_mode else DEFAULT_IMAGE_MODEL


def load_prompt_payload(prompt_file: str) -> tuple[str, dict | None]:
    raw = Path(prompt_file).read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw, None
    return json.dumps(payload, ensure_ascii=False, indent=2), payload if isinstance(payload, dict) else None


def guess_reference_mime_type(reference_image: str) -> str:
    guessed, _ = mimetypes.guess_type(reference_image)
    return guessed or "image/jpeg"


def build_generation_request(
    *,
    prompt_text: str,
    inline_parts: list[dict],
    aspect_ratio: str,
    model: str,
    image_size: str,
    output_mime_type: str,
) -> tuple[str, dict]:
    response_image_config: dict[str, str] = {"aspectRatio": aspect_ratio}
    if model != DEFAULT_DRAFT_MODEL:
        response_image_config["imageSize"] = image_size
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {
            "generationConfig": {"responseFormat": {"image": response_image_config}},
            "contents": [{"parts": [*inline_parts, {"text": prompt_text}]}],
        },
    )


def extract_image_part(payload: dict) -> dict:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise RuntimeError("Image generation returned no candidates")
    parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
    for part in parts:
        if not isinstance(part, dict):
            continue
        inline = part.get("inlineData") or part.get("inline_data")
        if isinstance(inline, dict) and inline.get("data"):
            return inline
    raise RuntimeError("Image generation returned no image data")


def save_generated_image(image_part: dict, output_file: str) -> dict[str, int | None]:
    image_bytes = base64.b64decode(image_part["data"])
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_bytes(image_bytes)

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            return {"width": image.width, "height": image.height}
    except Exception:
        return {"width": None, "height": None}


def write_generation_manifest(manifest_file: str, manifest: dict) -> None:
    manifest_path = Path(manifest_file)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_manifest_prompt(prompt_payload: dict | None, prompt_text: str) -> str:
    if not prompt_payload:
        return prompt_text
    prompt_value = prompt_payload.get("prompt")
    if isinstance(prompt_value, str) and prompt_value.strip():
        return prompt_value
    return prompt_text


def generate_image(
    prompt_file: str,
    reference_images: list[str],
    output_file: str,
    aspect_ratio: str = "16:9",
    *,
    model: str | None = None,
    image_size: str | None = None,
    output_mime_type: str | None = None,
    scientific_mode: bool = False,
    manifest_file: str | None = None,
    draft_mode: bool = False,
    timeout_seconds: int = 120,
) -> str:
    prompt_text, prompt_payload = load_prompt_payload(prompt_file)
    if scientific_mode:
        prompt_text = f"{SCIENTIFIC_GUARDRAIL}\n\n{prompt_text}"
    parts = []
    resolved_model = resolve_model_name(model, draft_mode=draft_mode)
    resolved_image_size = resolve_image_size(image_size, scientific_mode)
    resolved_output_mime_type = resolve_output_mime_type(output_file, output_mime_type, scientific_mode)
    
    # Filter out invalid reference images
    valid_reference_images = []
    for ref_img in reference_images:
        if validate_image(ref_img):
            valid_reference_images.append(ref_img)
        else:
            print(f"Skipping invalid reference image: {ref_img}")
    
    if len(valid_reference_images) < len(reference_images):
        print(f"Note: {len(reference_images) - len(valid_reference_images)} reference image(s) were skipped due to validation failure.")
    
    for reference_image in valid_reference_images:
        with open(reference_image, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        parts.append(
            {
                "inlineData": {
                    "mimeType": guess_reference_mime_type(reference_image),
                    "data": image_b64,
                }
            }
        )

    api_key = resolve_google_ai_studio_api_key()
    if not api_key:
        raise RuntimeError("Google AI Studio API key is not set. Configure GEMINI_API_KEY or GOOGLE_API_KEY.")

    url, request_payload = build_generation_request(
        prompt_text=prompt_text,
        inline_parts=parts,
        aspect_ratio=aspect_ratio,
        model=resolved_model,
        image_size=resolved_image_size,
        output_mime_type=resolved_output_mime_type,
    )
    response = requests.post(
        url,
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json=request_payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    image_part = extract_image_part(payload)
    actual_dimensions = save_generated_image(image_part, output_file)

    manifest_path = manifest_file or str(Path(output_file).with_name("generation_manifest.json"))
    manifest = {
        "model": resolved_model,
        "image_size": resolved_image_size,
        "output_mime_type": resolved_output_mime_type,
        "aspect_ratio": aspect_ratio,
        "scientific_mode": scientific_mode,
        "draft_mode": draft_mode,
        "prompt_file": prompt_file,
        "prompt": resolve_manifest_prompt(prompt_payload, prompt_text),
        "rendered_prompt": prompt_text,
        "negative_prompt": (prompt_payload or {}).get("negative_prompt") if prompt_payload else None,
        "figure_type": (prompt_payload or {}).get("figure_type") if prompt_payload else None,
        "references": valid_reference_images,
        "output_file": output_file,
        "actual_output": {
            "width": actual_dimensions["width"],
            "height": actual_dimensions["height"],
            "mime_type": image_part.get("mimeType") or image_part.get("mime_type") or resolved_output_mime_type,
        },
        "manifest_created_at": datetime.now(UTC).isoformat(),
        "retry_count": 0,
        "retried": False,
    }
    write_generation_manifest(manifest_path, manifest)
    return f"Successfully generated image to {output_file}. Manifest written to {manifest_path}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate images using Gemini API")
    parser.add_argument(
        "--prompt-file",
        required=True,
        help="Absolute path to JSON prompt file",
    )
    parser.add_argument(
        "--reference-images",
        nargs="*",
        default=[],
        help="Absolute paths to reference images (space-separated)",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output path for generated image",
    )
    parser.add_argument(
        "--aspect-ratio",
        required=False,
        default="16:9",
        help="Aspect ratio of the generated image",
    )
    parser.add_argument(
        "--model",
        required=False,
        default=None,
        help="Google AI Studio image generation model name",
    )
    parser.add_argument(
        "--image-size",
        required=False,
        default=None,
        help="Requested output size: 1K, 2K, or 4K",
    )
    parser.add_argument(
        "--output-mime-type",
        required=False,
        default=None,
        help="Requested output MIME type: image/png or image/jpeg",
    )
    parser.add_argument(
        "--scientific-mode",
        action="store_true",
        help="Enable scientific illustration guardrails and defaults",
    )
    parser.add_argument(
        "--manifest-file",
        required=False,
        default=None,
        help="Optional path for generation manifest JSON output",
    )
    parser.add_argument(
        "--draft-mode",
        action="store_true",
        help="Use lower-cost draft defaults when no model is explicitly provided",
    )

    args = parser.parse_args()

    try:
        print(
            generate_image(
                args.prompt_file,
                args.reference_images,
                args.output_file,
                args.aspect_ratio,
                model=args.model,
                image_size=args.image_size,
                output_mime_type=args.output_mime_type,
                scientific_mode=args.scientific_mode,
                manifest_file=args.manifest_file,
                draft_mode=args.draft_mode,
            )
        )
    except Exception as e:
        print(f"Error while generating image: {e}")

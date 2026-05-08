import base64
import json
import mimetypes
import os
import sys
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

try:
    from medrix_flow.utils import google_image as google_image_utils
except ModuleNotFoundError:
    harness_path = Path(__file__).resolve().parents[4] / "backend" / "packages" / "harness"
    if harness_path.exists():
        sys.path.insert(0, str(harness_path))
    from medrix_flow.utils import google_image as google_image_utils

IMAGE_PROVIDER_GOOGLE = "google-ai-studio"
IMAGE_PROVIDER_OPENAI = "openai-compatible"
DEFAULT_IMAGE_MODEL = "gemini-3-pro-image-preview"
DEFAULT_DRAFT_MODEL = google_image_utils.GOOGLE_IMAGE_SMOKE_MODEL
DEFAULT_IMAGE_SIZE = "2K"
SCIENTIFIC_IMAGE_SIZE = "4K"
DEFAULT_OUTPUT_MIME_TYPE = "image/jpeg"
SCIENTIFIC_OUTPUT_MIME_TYPE = "image/png"
SUPPORTED_IMAGE_SIZES = {"1K", "2K", "4K"}
SUPPORTED_OUTPUT_MIME_TYPES = {"image/jpeg", "image/png"}
SUPPORTED_OPENAI_COMPATIBLE_ASPECT_RATIOS = {"1:1", "16:9", "9:16"}
OPENAI_COMPATIBLE_SIZE_MAP = {
    "1:1": {"1K": "1024x1024", "2K": "2048x2048", "4K": "4096x4096"},
    "16:9": {"1K": "1024x576", "2K": "2048x1152", "4K": "4096x2304"},
    "9:16": {"1K": "576x1024", "2K": "1152x2048", "4K": "2304x4096"},
}
IMAGE_GEN_ACTIVE_PROVIDER_ENV = "IMAGE_GEN_ACTIVE_PROVIDER"
IMAGE_GEN_GOOGLE_MODEL_ENV = "IMAGE_GEN_GOOGLE_MODEL"
IMAGE_GEN_OPENAI_MODEL_ENV = "IMAGE_GEN_OPENAI_MODEL"
IMAGE_GEN_OPENAI_BASE_URL_ENV = "IMAGE_GEN_OPENAI_BASE_URL"
IMAGE_GEN_OPENAI_API_KEY_ENV = "IMAGE_GEN_OPENAI_API_KEY"
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


def get_non_empty_env_value(var_name: str) -> str | None:
    value = os.getenv(var_name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    return base_url.strip().rstrip("/") or None


def resolve_google_ai_studio_api_key() -> str | None:
    return get_non_empty_env_value("GEMINI_API_KEY") or get_non_empty_env_value("GOOGLE_API_KEY")


def resolve_openai_compatible_api_key() -> str | None:
    return get_non_empty_env_value(IMAGE_GEN_OPENAI_API_KEY_ENV)


def resolve_provider_name(provider: str | None) -> str:
    resolved_provider = provider or get_non_empty_env_value(IMAGE_GEN_ACTIVE_PROVIDER_ENV) or IMAGE_PROVIDER_GOOGLE
    if resolved_provider not in {IMAGE_PROVIDER_GOOGLE, IMAGE_PROVIDER_OPENAI}:
        raise ValueError(f"Unsupported provider: {resolved_provider}")
    return resolved_provider


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


def resolve_model_name(provider: str, model: str | None, draft_mode: bool = False) -> str:
    if model:
        return model
    if provider == IMAGE_PROVIDER_GOOGLE:
        if draft_mode:
            return DEFAULT_DRAFT_MODEL
        return get_non_empty_env_value(IMAGE_GEN_GOOGLE_MODEL_ENV) or DEFAULT_IMAGE_MODEL
    resolved = get_non_empty_env_value(IMAGE_GEN_OPENAI_MODEL_ENV)
    if not resolved:
        raise RuntimeError("OpenAI-compatible image provider model is not configured. Set IMAGE_GEN_OPENAI_MODEL or pass --model.")
    return resolved


def resolve_provider_base_url(provider: str, base_url: str | None) -> str | None:
    if provider != IMAGE_PROVIDER_OPENAI:
        return None
    resolved = normalize_base_url(base_url) or normalize_base_url(get_non_empty_env_value(IMAGE_GEN_OPENAI_BASE_URL_ENV))
    if not resolved:
        raise RuntimeError(
            "OpenAI-compatible image provider base URL is not configured. "
            "Set IMAGE_GEN_OPENAI_BASE_URL or pass --base-url."
        )
    return resolved


def resolve_provider_api_key(provider: str) -> str:
    if provider == IMAGE_PROVIDER_GOOGLE:
        api_key = resolve_google_ai_studio_api_key()
        if not api_key:
            raise RuntimeError("Google AI Studio API key is not set. Configure GEMINI_API_KEY or GOOGLE_API_KEY.")
        return api_key
    api_key = resolve_openai_compatible_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenAI-compatible image provider API key is not set. Configure IMAGE_GEN_OPENAI_API_KEY."
        )
    return api_key


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


def map_openai_compatible_size(aspect_ratio: str, image_size: str) -> str:
    if aspect_ratio not in SUPPORTED_OPENAI_COMPATIBLE_ASPECT_RATIOS:
        raise RuntimeError(
            f"OpenAI-compatible image provider does not support aspect ratio '{aspect_ratio}'. "
            "Supported values are 1:1, 16:9, and 9:16."
        )
    return OPENAI_COMPATIBLE_SIZE_MAP[aspect_ratio][image_size]


def build_openai_compatible_generation_request(
    *,
    prompt_text: str,
    model: str,
    image_size: str,
    aspect_ratio: str,
) -> dict:
    return {
        "model": model,
        "prompt": prompt_text,
        "n": 1,
        "size": map_openai_compatible_size(aspect_ratio, image_size),
        "response_format": "b64_json",
    }


def extract_openai_compatible_image(payload: dict, timeout_seconds: int) -> tuple[bytes, str | None]:
    data = payload.get("data") or []
    if not data:
        raise RuntimeError("OpenAI-compatible image provider returned no data")
    first = data[0] or {}
    if isinstance(first, dict):
        b64_payload = first.get("b64_json")
        if b64_payload:
            return base64.b64decode(b64_payload), None
        image_url = first.get("url")
        if image_url:
            response = requests.get(image_url, timeout=timeout_seconds)
            response.raise_for_status()
            return response.content, response.headers.get("Content-Type")
    raise RuntimeError("OpenAI-compatible image provider returned no image content")


def save_generated_image_bytes(image_bytes: bytes, output_file: str) -> dict[str, int | None]:
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
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
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
    resolved_provider = resolve_provider_name(provider)
    resolved_model = resolve_model_name(resolved_provider, model, draft_mode=draft_mode)
    resolved_base_url = resolve_provider_base_url(resolved_provider, base_url)
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

    if resolved_provider == IMAGE_PROVIDER_OPENAI and valid_reference_images:
        raise RuntimeError(
            "OpenAI-compatible image provider v1 does not support reference-guided image generation. "
            "Switch to Google AI Studio or remove reference images."
        )

    api_key = resolve_provider_api_key(resolved_provider)
    actual_mime_type = resolved_output_mime_type
    retry_count = 0
    if resolved_provider == IMAGE_PROVIDER_GOOGLE:
        result = google_image_utils.execute_google_image_request(
            requests_module=requests,
            api_key=api_key,
            model=resolved_model,
            prompt_text=prompt_text,
            inline_parts=parts,
            aspect_ratio=aspect_ratio,
            image_size=resolved_image_size,
            timeout_seconds=timeout_seconds,
        )
        payload = result.payload
        retry_count = result.retry_count
        image_part = google_image_utils.extract_google_image_part(payload)
        actual_mime_type = image_part.get("mimeType") or image_part.get("mime_type") or resolved_output_mime_type
        image_bytes = base64.b64decode(image_part["data"])
    else:
        response = requests.post(
            f"{resolved_base_url}/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=build_openai_compatible_generation_request(
                prompt_text=prompt_text,
                model=resolved_model,
                image_size=resolved_image_size,
                aspect_ratio=aspect_ratio,
            ),
            timeout=timeout_seconds,
        )
        try:
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                f"OpenAI-compatible image provider rejected {map_openai_compatible_size(aspect_ratio, resolved_image_size)} output for model '{resolved_model}'."
            ) from exc
        payload = response.json()
        image_bytes, actual_mime_type = extract_openai_compatible_image(payload, timeout_seconds)
        actual_mime_type = actual_mime_type or resolved_output_mime_type

    actual_dimensions = save_generated_image_bytes(image_bytes, output_file)

    manifest_path = manifest_file or str(Path(output_file).with_name("generation_manifest.json"))
    config_source = "explicit-override" if any([provider, model, base_url]) else "settings-default"
    manifest = {
        "provider": resolved_provider,
        "model": resolved_model,
        "resolved_model": resolved_model,
        "resolved_base_url": resolved_base_url,
        "config_source": config_source,
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
            "mime_type": actual_mime_type,
        },
        "manifest_created_at": datetime.now(UTC).isoformat(),
        "retry_count": retry_count,
        "retried": retry_count > 0,
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
        "--provider",
        required=False,
        default=None,
        help="Image provider override: google-ai-studio or openai-compatible",
    )
    parser.add_argument(
        "--model",
        required=False,
        default=None,
        help="Google AI Studio image generation model name",
    )
    parser.add_argument(
        "--base-url",
        required=False,
        default=None,
        help="OpenAI-compatible image generation base URL override",
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
                provider=args.provider,
                model=args.model,
                base_url=args.base_url,
                image_size=args.image_size,
                output_mime_type=args.output_mime_type,
                scientific_mode=args.scientific_mode,
                manifest_file=args.manifest_file,
                draft_mode=args.draft_mode,
            )
        )
    except Exception as e:
        print(f"Error while generating image: {e}")

from __future__ import annotations

import base64
import io
import time

from PIL import Image

import config


def validate_image(file) -> Image.Image:
    if file.type not in config.ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Unsupported image type: {file.type}. Use JPEG, PNG, or WebP.")
    size_mb = len(file.getvalue()) / (1024 * 1024)
    if size_mb > config.MAX_IMAGE_MB:
        raise ValueError(f"Image too large ({size_mb:.1f} MB). Max is {config.MAX_IMAGE_MB} MB.")
    return Image.open(io.BytesIO(file.getvalue())).convert("RGB")


def encode_image_base64(image: Image.Image) -> tuple[str, str]:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    b64 = base64.standard_b64encode(buf.getvalue()).decode()
    return b64, "image/jpeg"


def persist_image(image: Image.Image, meal_id: int) -> str:
    """Upload image to Supabase Storage and return the public URL."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    filename = f"{meal_id}_{int(time.time())}.jpg"

    if config.SUPABASE_URL and config.SUPABASE_KEY:
        from supabase import create_client
        sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        sb.storage.from_(config.SUPABASE_BUCKET).upload(
            filename,
            buf.getvalue(),
            {"content-type": "image/jpeg"},
        )
        return sb.storage.from_(config.SUPABASE_BUCKET).get_public_url(filename)

    # Local fallback (for development without Supabase)
    config.UPLOADS_DIR.mkdir(exist_ok=True)
    path = config.UPLOADS_DIR / filename
    image.save(str(path), format="JPEG", quality=85)
    return f"uploads/{filename}"

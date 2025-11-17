# app/utils/images.py
import os
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from urllib.parse import urlparse
from app.core.config import settings

def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

async def save_image(file: UploadFile, subdir: str) -> str:
    """
    Save uploaded file into UPLOAD_DIR/subdir and return the RELATIVE path
    used by StaticFiles mount, e.g. "owners/xxxx.jpg" or "vehicles/<owner>/<vehicle>/xxxx.jpg".
    """
    ensure_dir(settings.UPLOAD_DIR)
    full_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    ensure_dir(full_dir)

    # Keep original extension if present; default to .jpg
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    fname = f"{uuid4().hex}{ext}"
    fpath = os.path.join(full_dir, fname)

    # Write bytes
    with open(fpath, "wb") as out:
        out.write(await file.read())

    # return relative path (no host or /static prefix)
    return f"{subdir}/{fname}"

def make_public_url(request, stored_value: str | None) -> str | None:
    """
    Convert a stored image value into an absolute URL using the request host:

    - If stored_value is None -> None
    - If stored_value is an absolute URL containing "/static/<path>", extract <path>
      and build request.url_for("static", path=<path>)
    - If stored_value is already a relative path like "owners/x.jpg", build request.url_for("static", path=stored_value)
    """
    if not stored_value:
        return None

    parsed = urlparse(stored_value)
    if parsed.scheme in ("http", "https"):
        # try to extract the part after '/static/'
        if "/static/" in parsed.path:
            rel = parsed.path.split("/static/", 1)[1]
            return str(request.url_for("static", path=rel))
        # fallback: return stored_value as-is (rare)
        return stored_value

    # relative path
    return str(request.url_for("static", path=stored_value))

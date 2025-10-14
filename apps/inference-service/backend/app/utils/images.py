import os
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from app.core.config import settings

def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

async def save_image(file: UploadFile, subdir: str) -> str:
    ensure_dir(settings.UPLOAD_DIR)
    full_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    ensure_dir(full_dir)
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    fname = f"{uuid4().hex}{ext}"
    fpath = os.path.join(full_dir, fname)
    with open(fpath, "wb") as out:
        out.write(await file.read())
    return f"{settings.BASE_URL}/static/{subdir}/{fname}"

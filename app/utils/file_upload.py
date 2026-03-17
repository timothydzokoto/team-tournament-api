import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
from dotenv import load_dotenv
import os

load_dotenv()

UPLOADS_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(5 * 1024 * 1024)).split("#")[0].strip())
UPLOADS_DIR.mkdir(exist_ok=True)

# Create subdirectories
IMAGES_DIR = UPLOADS_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

PLAYERS_DIR = IMAGES_DIR / "players"
PLAYERS_DIR.mkdir(exist_ok=True)

TEAMS_DIR = IMAGES_DIR / "teams"
TEAMS_DIR.mkdir(exist_ok=True)

def save_image_file(file: UploadFile, subdirectory: str = "players", content: Optional[bytes] = None) -> str:
    """Save an uploaded image file and return the file path"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        file_content = content if content is not None else file.file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File exceeds max size of {MAX_FILE_SIZE} bytes")

        if not validate_image_bytes(file_content):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Determine save directory
        if subdirectory == "players":
            save_dir = PLAYERS_DIR
        elif subdirectory == "teams":
            save_dir = TEAMS_DIR
        else:
            save_dir = IMAGES_DIR
        
        # Save file
        file_path = save_dir / unique_filename
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        return str(file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def delete_file(file_path: str) -> bool:
    """Delete a file from the filesystem"""
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False

def get_file_url(file_path: str) -> str:
    """Convert file path to URL"""
    if not file_path:
        return ""

    path = Path(file_path)
    parts = list(path.parts)

    if "uploads" in parts:
        rel_parts = parts[parts.index("uploads") + 1 :]
    else:
        rel_parts = parts

    relative_path = "/".join(part for part in rel_parts if part)
    return f"/uploads/{relative_path}" if relative_path else "/uploads"

def validate_image_file(file: UploadFile) -> bool:
    """Validate that the uploaded file is a valid image"""
    try:
        # Check content type
        if not file.content_type or not file.content_type.startswith("image/"):
            return False
        
        # Try to open with PIL
        content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        return validate_image_bytes(content)
    except Exception:
        return False


def validate_image_bytes(content: bytes) -> bool:
    """Validate image bytes and enforce the configured max upload size."""
    try:
        if not content or len(content) > MAX_FILE_SIZE:
            return False
        image = Image.open(io.BytesIO(content))
        image.verify()
        return True
    except Exception:
        return False

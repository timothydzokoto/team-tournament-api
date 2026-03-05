import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads")
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
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
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
            file_content = content if content is not None else file.file.read()
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
        if not file.content_type.startswith("image/"):
            return False
        
        # Try to open with PIL
        content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        Image.open(io.BytesIO(content))
        return True
    except Exception:
        return False 

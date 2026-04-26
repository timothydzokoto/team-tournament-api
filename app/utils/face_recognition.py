try:
    import face_recognition
except ImportError:  # Optional dependency in this project
    face_recognition = None
import numpy as np
import json
from typing import List, Optional, Tuple
import io


class FaceRecognitionError(Exception):
    """Base exception for face-recognition analysis failures."""


class NoFaceDetectedError(FaceRecognitionError):
    """Raised when an image contains no detectable face."""


class MultipleFacesDetectedError(FaceRecognitionError):
    """Raised when an image contains more than one face."""


class FaceImageDecodeError(FaceRecognitionError):
    """Raised when an image cannot be decoded for face analysis."""


def is_face_recognition_available() -> bool:
    """Return whether the optional face_recognition dependency is installed."""
    return face_recognition is not None

def encode_face(image_path: str) -> Optional[np.ndarray]:
    """Encode a face from an image file"""
    if face_recognition is None:
        return None
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        return encodings[0] if encodings else None
    except Exception as e:
        print(f"Error encoding face: {e}")
        return None

def encode_face_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """Encode a face from image bytes"""
    if face_recognition is None:
        return None
    try:
        image = face_recognition.load_image_file(io.BytesIO(image_bytes))
        face_locations = face_recognition.face_locations(image)
        if not face_locations:
            raise NoFaceDetectedError("No face detected in the image")
        if len(face_locations) > 1:
            raise MultipleFacesDetectedError("Multiple faces detected in the image")

        encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
        if not encodings:
            raise NoFaceDetectedError("No face detected in the image")
        return encodings[0]
    except FaceRecognitionError:
        raise
    except Exception as e:
        raise FaceImageDecodeError(f"Error encoding face from bytes: {e}") from e

def compare_faces(known_encoding: np.ndarray, unknown_encoding: np.ndarray, tolerance: float = 0.6) -> bool:
    """Compare two face encodings"""
    if face_recognition is None:
        return False
    try:
        return face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=tolerance)[0]
    except Exception as e:
        print(f"Error comparing faces: {e}")
        return False

def find_best_match(unknown_encoding: np.ndarray, known_encodings: List[Tuple[int, np.ndarray]], tolerance: float = 0.6) -> Optional[Tuple[int, float]]:
    """Find the best matching face from a list of known encodings"""
    if face_recognition is None:
        return None
    if not known_encodings:
        return None
    
    try:
        # Get all known encodings
        encodings = [encoding for _, encoding in known_encodings]
        ids = [player_id for player_id, _ in known_encodings]
        
        # Calculate face distances
        face_distances = face_recognition.face_distance(encodings, unknown_encoding)
        
        # Find the best match
        best_match_index = np.argmin(face_distances)
        best_distance = face_distances[best_match_index]
        
        # Convert distance to confidence (lower distance = higher confidence)
        confidence = 1.0 - min(best_distance, 1.0)
        
        # Check if the match is within tolerance
        if best_distance <= tolerance:
            return (ids[best_match_index], confidence)
        
        return None
    except Exception as e:
        print(f"Error finding best match: {e}")
        return None

def save_face_encoding(encoding: np.ndarray) -> str:
    """Save face encoding as JSON string"""
    try:
        return json.dumps(encoding.tolist())
    except Exception as e:
        print(f"Error saving face encoding: {e}")
        return ""

def load_face_encoding(encoding_str: str) -> Optional[np.ndarray]:
    """Load face encoding from JSON string"""
    try:
        if not encoding_str:
            return None
        encoding_list = json.loads(encoding_str)
        return np.array(encoding_list)
    except Exception as e:
        print(f"Error loading face encoding: {e}")
        return None

def validate_image(image_bytes: bytes) -> bool:
    """Validate that the image contains a face"""
    try:
        encoding = encode_face_from_bytes(image_bytes)
        return encoding is not None
    except FaceRecognitionError:
        return False

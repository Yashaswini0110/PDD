import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import threading

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
METADATA_FILE = os.path.join(UPLOADS_DIR, "metadata.json")

os.makedirs(UPLOADS_DIR, exist_ok=True)

# Thread-safe lock for metadata access
_metadata_lock = threading.Lock()

if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "w") as f:
        json.dump({}, f)

def _load_metadata() -> Dict:
    with _metadata_lock:
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}

def _save_metadata(metadata: Dict) -> None:
    with _metadata_lock:
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=4)

def _secure_join(base, filename):
    """Safely join a base directory and a filename to prevent path traversal."""
    # Sanitize the filename to prevent directory traversal
    filename = os.path.basename(filename)
    # Join the base directory and the sanitized filename
    return os.path.join(base, filename)

def generate_object_name(original_filename: str) -> str:
    name, ext = os.path.splitext(original_filename)
    return f"{uuid.uuid4().hex}{ext.lower()}"

def get_local_path(object_name: str) -> str:
    return _secure_join(UPLOADS_DIR, object_name)

def file_exists(object_name: str) -> bool:
    return os.path.exists(get_local_path(object_name))

def save_bytes(object_name: str, data: bytes) -> None:
    with open(get_local_path(object_name), "wb") as f:
        f.write(data)

def delete_file(object_name: str) -> bool:
    """Delete a file and its metadata"""
    path = get_local_path(object_name)
    if not os.path.exists(path):
        return False
    
    os.remove(path)
    
    metadata = _load_metadata()
    if object_name in metadata:
        del metadata[object_name]
        _save_metadata(metadata)
    
    return True

def set_expiration(object_name: str, expiration_time: datetime) -> None:
    metadata = _load_metadata()
    metadata[object_name] = {
        "expires_at": expiration_time.isoformat()
    }
    _save_metadata(metadata)

def delete_expired_files() -> None:
    """Delete files that have passed their expiration time"""
    metadata = _load_metadata()
    now = datetime.now()
    to_delete = [
        name for name, data in metadata.items()
        if now > datetime.fromisoformat(data["expires_at"])
    ]
    
    for object_name in to_delete:
        path = get_local_path(object_name)
        if os.path.exists(path):
            os.remove(path)
        del metadata[object_name]
    
    _save_metadata(metadata)

def mtime(object_name: str) -> Optional[datetime]:
    path = get_local_path(object_name)
    if os.path.exists(path):
        return datetime.fromtimestamp(os.path.getmtime(path))
    return None

def is_older_than(object_name: str, delta: timedelta) -> bool:
    modified = mtime(object_name)
    if not modified:
        return False
    return datetime.now() - modified > delta

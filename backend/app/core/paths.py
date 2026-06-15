from pathlib import Path
from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

if settings.user_data_dir:
    _BASE = Path(settings.user_data_dir).resolve()
else:
    _BASE = PROJECT_ROOT / "static"

STATIC_DIR = _BASE
UPLOADS_DIR = STATIC_DIR / "uploads"
GENERATIONS_DIR = STATIC_DIR / "generations"
EDITS_DIR = STATIC_DIR / "edits"
VIDEOS_DIR = STATIC_DIR / "videos"
AVATARS_DIR = STATIC_DIR / "avatars"


def resolve_path(file_path: str) -> Path:
    """Resolve a stored relative path (e.g. 'static/knowledge/x.pdf') against STATIC_DIR."""
    p = Path(file_path)
    if p.is_absolute():
        return p
    if p.parts and p.parts[0] == "static":
        return STATIC_DIR / Path(*p.parts[1:])
    return STATIC_DIR / p

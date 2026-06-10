from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

UPLOADS_DIR = STATIC_DIR / "uploads"
GENERATIONS_DIR = STATIC_DIR / "generations"
EDITS_DIR = STATIC_DIR / "edits"
VIDEOS_DIR = STATIC_DIR / "videos"
AVATARS_DIR = STATIC_DIR / "avatars"

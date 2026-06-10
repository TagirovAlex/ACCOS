#!/usr/bin/env python3
"""Migrate files from old paths to new structure.

Old → New:
  static/generated/<gen_id>/<file>  →  static/generations/<user_id>/<gen_id>/<file>
  static/uploads/<session_id>/<file> →  static/uploads/<user_id>/<file>  (best-effort)

Run from project root:  .venv/bin/python scripts/migrate_files.py
"""
import asyncio
import json
import shutil
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.paths import (
    PROJECT_ROOT, GENERATIONS_DIR, UPLOADS_DIR,
    STATIC_DIR,
)
from app.db.session import async_session_factory
from app.repositories.generation_repository import GenerationRepository
from app.db.models.image_asset import ImageAsset
from app.db.models.generation import GenerationRecord
from sqlalchemy import select
from uuid import UUID

OLD_GENERATED = STATIC_DIR / "generated"


async def migrate_image_assets():
    """Move DB-referenced assets to new paths."""
    async with async_session_factory() as session:
        rows = (await session.execute(select(ImageAsset))).scalars().all()
        for asset in rows:
            fp = asset.file_path
            if not fp:
                continue
            if fp.startswith("static/generated/"):
                parts = fp.split("/")
                # static/generated/<gen_id>/<filename>
                gen_id = parts[2]
                filename = parts[3]
                uid = str(asset.user_id)
                new_rel = f"static/generations/{uid}/{gen_id}/{filename}"
                old_abs = STATIC_DIR / "generated" / gen_id / filename
                new_abs = GENERATIONS_DIR / uid / gen_id / filename
                if old_abs.exists():
                    new_abs.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(old_abs), str(new_abs))
                    asset.file_path = new_rel
                    print(f"  Moved: {old_abs} → {new_abs}")
                else:
                    asset.file_path = new_rel
                    print(f"  File not found, updating DB only: {fp} → {new_rel}")
        await session.flush()
        print(f"  Updated {len(rows)} assets")


async def migrate_old_generated_dirs():
    """Move orphaned generated/ dirs (no DB record) to new structure.

    We probe GenerationRecord for user_id if available, else use 'unknown'.
    """
    old_dirs = sorted(OLD_GENERATED.iterdir()) if OLD_GENERATED.is_dir() else []
    if not old_dirs:
        print("  No old generated/ dirs found.")
        return

    async with async_session_factory() as session:
        for old_dir in old_dirs:
            gen_id = old_dir.name
            # Try to find the generation record
            record = (await session.execute(
                select(GenerationRecord).where(GenerationRecord.id == UUID(gen_id))
            )).scalar_one_or_none()
            uid = str(record.user_id) if record else "unknown"
            new_dir = GENERATIONS_DIR / uid / gen_id
            new_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_dir), str(new_dir))
            print(f"  Moved dir: {old_dir} → {new_dir}")


async def main():
    print("=== Migrating image_assets ===")
    await migrate_image_assets()
    print()
    print("=== Migrating orphaned generated/ dirs ===")
    await migrate_old_generated_dirs()
    print()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

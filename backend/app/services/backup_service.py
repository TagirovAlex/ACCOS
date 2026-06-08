import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)

FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
BACKUP_PREFIX = "accos_backup_"
BACKUP_SUFFIX = ".sql.gz"


class BackupService:
    def __init__(self):
        self.backup_dir = Path.cwd() / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def list_backups(self) -> list[dict]:
        backups = []
        for f in sorted(self.backup_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.is_file() and f.name.startswith(BACKUP_PREFIX) and f.name.endswith(BACKUP_SUFFIX):
                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "path": str(f.absolute()),
                })
        return backups

    async def create_backup(self) -> dict:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{BACKUP_PREFIX}{timestamp}{BACKUP_SUFFIX}"
        filepath = self.backup_dir / filename

        cmd = [
            "pg_dump",
            f"--host={settings.DB_HOST}",
            f"--port={settings.DB_PORT}",
            f"--dbname={settings.DB_NAME}",
            f"--username={settings.DB_USER}",
            "--no-password",
            "--format=c",
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DB_PASSWORD

        try:
            with open(filepath, "wb") as f:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=f,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                )
                _, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else "Unknown error"
                logger.error(f"pg_dump failed: {error_msg}")
                if filepath.exists():
                    filepath.unlink()
                return {"success": False, "error": error_msg}

            stat = filepath.stat()
            logger.info(f"Backup created: {filename} ({stat.st_size} bytes)")
            return {
                "success": True,
                "filename": filename,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        except FileNotFoundError:
            error_msg = "pg_dump not found. Ensure PostgreSQL client tools are installed."
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.exception(f"Backup failed: {e}")
            if filepath.exists():
                filepath.unlink()
            return {"success": False, "error": str(e)}

    async def delete_backup(self, filename: str) -> dict:
        filepath = await self.get_backup_path(filename)
        if not filepath:
            return {"success": False, "error": f"Backup '{filename}' not found"}
        try:
            filepath.unlink()
            logger.info(f"Backup deleted: {filename}")
            return {"success": True}
        except Exception as e:
            logger.exception(f"Failed to delete backup {filename}: {e}")
            return {"success": False, "error": str(e)}

    async def get_backup_path(self, filename: str) -> Path | None:
        if not FILENAME_PATTERN.match(filename):
            logger.warning(f"Invalid backup filename (path traversal attempt?): {filename}")
            return None
        filepath = self.backup_dir / filename
        if filepath.exists() and filepath.is_file():
            return filepath
        return None

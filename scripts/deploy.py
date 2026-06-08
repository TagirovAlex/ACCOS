#!/usr/bin/env python3
"""Deploy ACCOS to 10.0.68.43 via native SSH/SCP."""
import subprocess
import tarfile
from pathlib import Path

HOST = "root@10.0.68.43"
KEY = str(Path.home() / ".ssh" / "accos_deploy")

EXCLUDE = {
    ".venv", "node_modules", "__pycache__", ".pytest_cache",
    ".git", ".env", "scripts/deploy.sh", "scripts/deploy.py",
}

SSH = f'ssh -i "{KEY}" -o StrictHostKeyChecking=no {HOST}'
SCP = f'scp -i "{KEY}" -o StrictHostKeyChecking=no'


def filter_tar(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    parts = tarinfo.name.split("/")
    for pat in EXCLUDE:
        if pat in parts:
            return None
    if tarinfo.name.endswith(".pyc"):
        return None
    return tarinfo


def run(cmd: str, timeout: int = 120) -> bool:
    print(f"> {cmd[:120]}")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if r.stdout.strip():
            for line in r.stdout.strip().splitlines()[:20]:
                print(f"  {line}")
        if r.returncode != 0 and r.stderr.strip():
            for line in r.stderr.strip().splitlines()[:10]:
                print(f"  ! {line}")
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print("  Timeout")
        return False


def deploy():
    project_root = Path(__file__).parent.parent
    script_path = project_root / "scripts" / "deploy.sh"

    print("Creating archive...")
    archive = Path(project_root / "scripts" / "accos_deploy.tar.gz")
    with tarfile.open(str(archive), mode="w:gz") as tar:
        tar.add(str(project_root), arcname="accos", filter=filter_tar)
    mb = archive.stat().st_size / 1024 / 1024
    print(f"Archive: {mb:.1f} MB")

    print("Uploading archive...")
    run(f'{SCP} "{archive}" {HOST}:/tmp/accos.tar.gz', 120)

    print("Uploading deploy script...")
    run(f'{SCP} "{script_path}" {HOST}:/tmp/deploy.sh', 10)

    print("Running deploy...")
    run(f'{SSH} bash /tmp/deploy.sh', 600)

    archive.unlink()
    print("Done")


if __name__ == "__main__":
    deploy()

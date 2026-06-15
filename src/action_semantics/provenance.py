from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io_utils import sha256_file


def current_git_commit(repo_dir: Path | None = None) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def build_manifest(
    *,
    command: str,
    input_files: list[Path],
    output_files: list[Path],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "parameters": parameters,
        "python": sys.version,
        "platform": platform.platform(),
        "git_commit": current_git_commit(Path.cwd()),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in input_files
            if path.exists()
        ],
        "outputs": [
            {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in output_files
            if path.exists()
        ],
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")

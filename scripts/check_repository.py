from __future__ import annotations

from pathlib import Path

from action_semantics.verification import verify_output_repository


if __name__ == "__main__":
    verify_output_repository(Path.cwd())

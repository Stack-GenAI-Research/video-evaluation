"""Decide whether generated IndexedVideo features are safe to reuse."""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from .io_utils import sha256_file, sha256_json_obj
from .retrieval.scorers import STRUCTURED_SCORER_VERSION


INDEX_SCHEMA_VERSION = "indexed-video-segments-v2"
_PACKAGE_ROOT = Path(__file__).resolve().parent
_BUILD_CODE_PATHS = (
    "indexed_videos.py",
    "models.py",
    "month1.py",
    "month2.py",
    "sample_analysis.py",
    "taxonomy.py",
    "text.py",
    "extraction/framenet.py",
    "extraction/srl.py",
    "extraction/triples.py",
    "extraction/verbnet.py",
)


def _installed_version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def index_build_code_sha256() -> str:
    """Hash every source module that changes generated index features."""
    hashes = {
        relative: sha256_file(_PACKAGE_ROOT / relative)
        for relative in _BUILD_CODE_PATHS
    }
    return sha256_json_obj(hashes)


def index_build_versions(spacy_model: str) -> dict[str, Any]:
    return {
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "scorer_version": STRUCTURED_SCORER_VERSION,
        "index_build_code_sha256": index_build_code_sha256(),
        "spacy_version": _installed_version("spacy"),
        "spacy_model": spacy_model,
        "spacy_model_version": _installed_version(spacy_model.replace("_", "-")),
    }


def index_staleness_reasons(
    *,
    source_jsonl: Path,
    output_dir: Path,
    spacy_model: str,
) -> list[str]:
    """Return concrete reasons an existing index must be rebuilt."""
    manifest_path = output_dir / "index_manifest.json"
    if not source_jsonl.is_file():
        return [f"source file is missing: {source_jsonl}"]
    if not manifest_path.is_file():
        return [f"index manifest is missing: {manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeError) as exc:
        return [f"index manifest cannot be read: {exc}"]
    if not isinstance(manifest, dict):
        return ["index manifest is not a JSON object"]

    reasons: list[str] = []
    inputs = manifest.get("inputs", [])
    source_hash = sha256_file(source_jsonl)
    if not isinstance(inputs, list) or not any(
        isinstance(row, dict) and row.get("sha256") == source_hash for row in inputs
    ):
        reasons.append("source JSONL hash changed")

    parameters = manifest.get("parameters", {})
    expected_parameters = index_build_versions(spacy_model)
    if not isinstance(parameters, dict):
        reasons.append("manifest parameters are missing")
    else:
        for key, expected in expected_parameters.items():
            if parameters.get(key) != expected:
                reasons.append(
                    f"{key} changed (index={parameters.get(key)!r}, current={expected!r})"
                )

    outputs = manifest.get("outputs", [])
    if not isinstance(outputs, list) or not outputs:
        reasons.append("manifest output hashes are missing")
    else:
        for row in outputs:
            if not isinstance(row, dict):
                reasons.append("manifest contains an invalid output entry")
                continue
            path_value = row.get("path")
            expected_hash = row.get("sha256")
            path = Path(path_value) if isinstance(path_value, str) else None
            if path is None or not path.is_file():
                reasons.append(f"generated artifact is missing: {path_value}")
            elif not isinstance(expected_hash, str) or sha256_file(path) != expected_hash:
                reasons.append(f"generated artifact hash changed: {path}")
    return reasons

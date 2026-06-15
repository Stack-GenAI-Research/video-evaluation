from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .io_utils import iter_jsonl, sha256_file


class DataQualityError(RuntimeError):
    pass


def _duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted([value for value, count in counts.items() if count > 1])


def validate_jsonl_basic(path: Path, id_field: str, required_fields: list[str]) -> dict[str, Any]:
    row_count = 0
    ids: list[str] = []
    missing: Counter[str] = Counter()
    for row in iter_jsonl(path):
        row_count += 1
        for field in required_fields:
            if row.get(field) in (None, ""):
                missing[field] += 1
        value = row.get(id_field)
        if value not in (None, ""):
            ids.append(str(value))
    duplicate_ids = _duplicate_values(ids)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "row_count": row_count,
        "id_field": id_field,
        "unique_ids": len(set(ids)),
        "duplicate_ids": duplicate_ids[:50],
        "duplicate_id_count": len(duplicate_ids),
        "missing_required_counts": dict(missing),
    }


def require_nonempty_report(report: dict[str, Any], artifact_name: str) -> None:
    if int(report.get("row_count", 0)) <= 0:
        raise DataQualityError(f"{artifact_name} has zero rows; refusing to treat it as completed real data.")
    if int(report.get("duplicate_id_count", 0)) > 0:
        raise DataQualityError(f"{artifact_name} has duplicate IDs: {report.get('duplicate_ids')}")
    missing = report.get("missing_required_counts") or {}
    bad = {key: value for key, value in missing.items() if int(value) > 0}
    if bad:
        raise DataQualityError(f"{artifact_name} has missing required fields: {bad}")

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

import pandas as pd
from pydantic import BaseModel, ValidationError

from .models import ClipRecord, PairwiseComparison, StepRecord

T = TypeVar("T", bound=BaseModel)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json_obj(obj: Any) -> str:
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} line {line_number}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"Expected JSON object in {path} line {line_number}")
            obj.setdefault("source_row_sha256", sha256_json_obj(obj))
            yield obj


def read_jsonl_model(path: Path, model_type: type[T]) -> list[T]:
    rows: list[T] = []
    errors: list[str] = []
    for row_number, obj in enumerate(iter_jsonl(path), start=1):
        try:
            rows.append(model_type.model_validate(obj))
        except ValidationError as exc:
            errors.append(f"row {row_number}: {exc}")
            if len(errors) >= 20:
                break
    if errors:
        joined = "\n".join(errors)
        raise ValueError(f"{path} failed validation for {model_type.__name__}:\n{joined}")
    return rows


def read_clips(path: Path) -> list[ClipRecord]:
    return read_jsonl_model(path, ClipRecord)


def read_steps(path: Path) -> list[StepRecord]:
    return read_jsonl_model(path, StepRecord)


def read_pairwise(path: Path) -> list[PairwiseComparison]:
    return read_jsonl_model(path, PairwiseComparison)


def write_jsonl(path: Path, rows: Iterable[BaseModel | dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            if isinstance(row, BaseModel):
                data = row.model_dump(mode="json")
            else:
                data = row
            fh.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_list = list(rows)
    if not rows_list:
        if fieldnames is None:
            raise ValueError(f"Refusing to write empty CSV without fieldnames: {path}")
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
        return 0
    if fieldnames is None:
        all_fields: list[str] = []
        for row in rows_list:
            for key in row:
                if key not in all_fields:
                    all_fields.append(key)
        fieldnames = all_fields
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows_list:
            writer.writerow(row)
    return len(rows_list)


def read_jsonl_as_dataframe(path: Path) -> pd.DataFrame:
    rows = list(iter_jsonl(path))
    return pd.DataFrame(rows)

"""Prepare the nested IndexedVideo sample for the structured-analysis pipeline.

The private sample is a video-level export.  The retrieval pipeline, on the
other hand, expects one record per indexed clip.  This module makes that
conversion explicit and keeps the fields that came from the source dataset
separate from fields derived by this repository.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .io_utils import iter_jsonl, write_jsonl
from .text import normalize_text


def _as_string_list(value: Any) -> list[str]:
    """Turn simple or Gemini-annotated inventory text into primary item names."""
    if value is None:
        return []
    if isinstance(value, list):
        values = value
    else:
        text = str(value)
        if " used for " in text.lower() or " alternatives:" in text.lower():
            values = re.split(r"\.\s*,\s*(?=[A-Z0-9])", text)
        else:
            values = text.split(",")
    output: list[str] = []
    for item in values:
        primary = re.split(r"\s+alternatives:|\s+used for", str(item), maxsplit=1, flags=re.I)[0]
        primary = re.sub(r"\s+(unknown|not specified)$", "", primary, flags=re.I)
        if cleaned := normalize_text(primary).rstrip("."):
            output.append(cleaned)
    return output


def _source_video_id(row: dict[str, Any], row_number: int) -> str:
    value = row.get("video_id")
    if value in (None, ""):
        raise ValueError(f"Indexed video row {row_number} has no video_id")
    return str(value)


def flatten_indexed_videos(source_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Flatten nested video clips and return a transparent coverage profile.

    The function deliberately does not manufacture step records, dense
    embeddings, or relevance labels.  Those values are required for Month 3
    retrieval evaluation and are not available in this sample export.
    """
    clips: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    video_count = 0
    clips_with_description = 0
    clips_with_goal = 0
    clips_with_tools = 0
    clips_with_supplies = 0

    for row_number, row in enumerate(iter_jsonl(source_path), start=1):
        video_count += 1
        video_id = _source_video_id(row, row_number)
        nested_clips = row.get("clips")
        if not isinstance(nested_clips, list):
            raise ValueError(f"Indexed video row {row_number} has a non-list clips field")
        category = row.get("category")
        category_name = normalize_text(category.get("name")) if isinstance(category, dict) else ""
        if category_name:
            category_counts[category_name] += 1

        for clip_index, nested_clip in enumerate(nested_clips):
            if not isinstance(nested_clip, dict):
                raise ValueError(f"Indexed video row {row_number} clip {clip_index} is not an object")
            name = normalize_text(nested_clip.get("name"))
            if not name:
                raise ValueError(f"Indexed video row {row_number} clip {clip_index} has no name")
            description = normalize_text(nested_clip.get("description"))
            goal = normalize_text(nested_clip.get("goal"))
            tools = _as_string_list(nested_clip.get("tools"))
            supplies = _as_string_list(nested_clip.get("supplies"))
            clips_with_description += bool(description)
            clips_with_goal += bool(goal)
            clips_with_tools += bool(tools)
            clips_with_supplies += bool(supplies)

            # The ordinal is part of the source structure and makes the ID
            # stable even when two clips in one video have the same name.
            clip_id = f"indexed-video-{video_id}-clip-{clip_index:03d}"
            clips.append(
                {
                    "clip_id": clip_id,
                    "video_id": video_id,
                    "url": normalize_text(row.get("url")) or None,
                    "title": name,
                    "description": description or None,
                    "summary": goal or None,
                    "gemini_metadata": {
                        "source_video": {
                            "youtube_id": normalize_text(row.get("youtube_id")) or None,
                            "category": category_name or None,
                            "title": normalize_text(row.get("title")) or None,
                        },
                        "clip": {
                            "index": clip_index,
                            "start_seconds": nested_clip.get("start"),
                            "end_seconds": nested_clip.get("end"),
                            "tools": tools,
                            "supplies": supplies,
                            "source_tools_text": normalize_text(nested_clip.get("tools")) or None,
                            "source_supplies_text": normalize_text(nested_clip.get("supplies")) or None,
                        },
                    },
                    "dense_embeddings": {},
                    "source_row_sha256": row["source_row_sha256"],
                }
            )

    if not clips:
        raise ValueError(f"{source_path} did not contain any nested clip records")
    clip_count = len(clips)
    return clips, {
        "source_format": "indexed-videos-nested-jsonl-v1",
        "source_path": str(source_path),
        "video_count": video_count,
        "clip_count": clip_count,
        "category_counts": dict(sorted(category_counts.items())),
        "coverage": {
            "clip_description": clips_with_description / clip_count,
            "clip_goal": clips_with_goal / clip_count,
            "clip_tools": clips_with_tools / clip_count,
            "clip_supplies": clips_with_supplies / clip_count,
        },
        "month1_month2_ready": True,
        "month3_ready": False,
        "month3_blockers": [
            "No project-step records are included in indexed-videos-250.jsonl.",
            "No ClipPairComparison relevance labels are included in indexed-videos-250.jsonl.",
            "No dense embedding vectors are included in indexed-videos-250.jsonl.",
        ],
    }


def prepare_indexed_videos(source_path: Path, output_dir: Path) -> dict[str, Path]:
    """Write the flat clip export and its data-availability report."""
    clips, profile = flatten_indexed_videos(source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    clips_path = output_dir / "indexed_video_clips.jsonl"
    profile_path = output_dir / "indexed_video_profile.json"
    write_jsonl(clips_path, clips)
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True), encoding="utf-8")
    return {"clips": clips_path, "profile": profile_path}

"""Run the parts of the pipeline supported by the IndexedVideo sample."""

from __future__ import annotations

import json
from pathlib import Path

from .config import PipelineConfig
from .indexed_videos import prepare_indexed_videos
from .month1 import run_month1
from .month2 import run_month2
from .verification import verify_structured_analysis


def run_indexed_video_analysis(
    *,
    indexed_videos_jsonl: Path,
    output_dir: Path,
    spacy_model: str,
    random_seed: int,
    min_taxonomy_support: int,
) -> dict[str, Path]:
    """Flatten the real sample and run its valid Month 1/2 analysis path."""
    input_paths = prepare_indexed_videos(indexed_videos_jsonl, output_dir / "input")
    config = PipelineConfig(
        output_dir=output_dir,
        spacy_model=spacy_model,
        random_seed=random_seed,
        clip_limit=None,
    )
    month1 = run_month1(clips_jsonl=input_paths["clips"], steps_jsonl=None, config=config)
    month2 = run_month2(
        month1_dir=month1["month_dir"],
        config=config,
        min_taxonomy_support=min_taxonomy_support,
    )
    verification = verify_structured_analysis(output_dir)
    profile = json.loads(input_paths["profile"].read_text(encoding="utf-8"))
    summary = json.loads(month1["summary"].read_text(encoding="utf-8"))
    diagnostics = json.loads(month2["diagnostics"].read_text(encoding="utf-8"))
    report_path = output_dir / "sample_analysis_report.json"
    report_path.write_text(
        json.dumps(
            {
                "input_profile": profile,
                "month1": summary,
                "month2_taxonomy": diagnostics,
                "verification_artifacts": sorted(verification),
                "evaluation_status": (
                    "Month 3 was intentionally not run: this source has no steps, "
                    "pairwise labels, or dense embeddings."
                ),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return {"report": report_path, "profile": input_paths["profile"], **month1, **month2}

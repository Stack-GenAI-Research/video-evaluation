from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from action_semantics.config import PipelineConfig
from action_semantics.io_utils import read_clips, read_pairwise, read_steps, write_csv, write_jsonl
from action_semantics.models import PairwiseEvaluationRow, ScoreRow
from action_semantics.provenance import build_manifest, write_manifest
from action_semantics.retrieval.evaluation import predict_pairwise_winner, write_evaluation_summary
from action_semantics.retrieval.scorers import resources_from_files, score_step_clip


def _index_by_id(rows: list[Any], attr: str) -> dict[str, Any]:
    return {getattr(row, attr): row for row in rows}


def _score_needed_pairs(
    *,
    steps_by_id: dict[str, Any],
    clips_by_id: dict[str, Any],
    comparisons: list[Any],
    month1_dir: Path,
    month2_dir: Path,
    dense_keys: list[str] | None,
    hybrid_alpha: float,
) -> dict[tuple[str, str], ScoreRow]:
    resources = resources_from_files(month1_dir, month2_dir)
    needed = sorted({(row.step_id, row.clip_a_id) for row in comparisons} | {(row.step_id, row.clip_b_id) for row in comparisons})
    output: dict[tuple[str, str], ScoreRow] = {}
    missing: list[tuple[str, str]] = []
    for step_id, clip_id in needed:
        step = steps_by_id.get(step_id)
        clip = clips_by_id.get(clip_id)
        if step is None or clip is None:
            missing.append((step_id, clip_id))
            continue
        output[(step_id, clip_id)] = score_step_clip(
            step,
            clip,
            resources,
            dense_keys=dense_keys,
            hybrid_alpha=hybrid_alpha,
        )
    if missing:
        preview = ", ".join(f"{step_id}/{clip_id}" for step_id, clip_id in missing[:10])
        raise ValueError(f"Pairwise comparisons reference missing step/clip records: {preview}")
    return output


def _pairwise_rows(
    comparisons: list[Any],
    scores: dict[tuple[str, str], ScoreRow],
    model_name: str,
) -> list[PairwiseEvaluationRow]:
    rows: list[PairwiseEvaluationRow] = []
    attr = f"{model_name}_score"
    for comparison in comparisons:
        score_a_row = scores[(comparison.step_id, comparison.clip_a_id)]
        score_b_row = scores[(comparison.step_id, comparison.clip_b_id)]
        score_a = getattr(score_a_row, attr)
        score_b = getattr(score_b_row, attr)
        predicted, tie = predict_pairwise_winner(score_a, score_b, comparison.clip_a_id, comparison.clip_b_id)
        rows.append(
            PairwiseEvaluationRow(
                comparison_id=comparison.comparison_id,
                step_id=comparison.step_id,
                clip_a_id=comparison.clip_a_id,
                clip_b_id=comparison.clip_b_id,
                winner_clip_id=comparison.winner_clip_id,
                model_name=model_name,
                score_a=float(score_a) if score_a is not None else None,
                score_b=float(score_b) if score_b is not None else None,
                predicted_winner_clip_id=predicted,
                correct=(predicted == comparison.winner_clip_id) if predicted is not None else None,
                tie=tie,
            )
        )
    return rows


def run_month3(
    *,
    clips_jsonl: Path,
    steps_jsonl: Path,
    pairwise_jsonl: Path,
    month1_dir: Path,
    month2_dir: Path,
    config: PipelineConfig,
    dense_keys: list[str] | None = None,
    hybrid_alpha: float = 0.5,
) -> dict[str, Path]:
    month_dir = config.ensure_output_dir() / "month3"
    month_dir.mkdir(parents=True, exist_ok=True)

    clips = read_clips(clips_jsonl)
    steps = read_steps(steps_jsonl)
    comparisons = read_pairwise(pairwise_jsonl)
    clips_by_id = _index_by_id(clips, "clip_id")
    steps_by_id = _index_by_id(steps, "step_id")

    scores = _score_needed_pairs(
        steps_by_id=steps_by_id,
        clips_by_id=clips_by_id,
        comparisons=comparisons,
        month1_dir=month1_dir,
        month2_dir=month2_dir,
        dense_keys=dense_keys,
        hybrid_alpha=hybrid_alpha,
    )

    score_rows = list(scores.values())
    by_model = {
        "dense": _pairwise_rows(comparisons, scores, "dense"),
        "structured": _pairwise_rows(comparisons, scores, "structured"),
        "hybrid": _pairwise_rows(comparisons, scores, "hybrid"),
    }

    scores_path = month_dir / "step_clip_scores.jsonl"
    scores_csv_path = month_dir / "step_clip_scores.csv"
    write_jsonl(scores_path, score_rows)
    write_csv(scores_csv_path, [row.model_dump(mode="json") for row in score_rows])

    pairwise_paths: dict[str, Path] = {}
    for model_name, rows in by_model.items():
        path = month_dir / f"pairwise_eval_{model_name}.jsonl"
        write_jsonl(path, rows)
        pairwise_paths[model_name] = path

    summary_path = month_dir / "evaluation_summary.json"
    write_evaluation_summary(summary_path, by_model, seed=config.random_seed)

    output_files = [scores_path, scores_csv_path, summary_path, *pairwise_paths.values()]
    manifest_path = month_dir / "manifest.json"
    write_manifest(
        manifest_path,
        build_manifest(
            command="run-month3",
            input_files=[clips_jsonl, steps_jsonl, pairwise_jsonl],
            output_files=output_files,
            parameters={
                "dense_keys": dense_keys,
                "hybrid_alpha": hybrid_alpha,
                "random_seed": config.random_seed,
                "comparison_rows": len(comparisons),
            },
        ),
    )
    return {
        "month_dir": month_dir,
        "scores": scores_path,
        "scores_csv": scores_csv_path,
        "summary": summary_path,
        "manifest": manifest_path,
        **{f"pairwise_{key}": value for key, value in pairwise_paths.items()},
    }

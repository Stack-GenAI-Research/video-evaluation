from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .quality import DataQualityError, require_nonempty_report, validate_jsonl_basic


REQUIRED_ARTIFACTS = {
    # relative path: (id field used for reporting, required fields, duplicate IDs allowed)
    "month1/action_object_tool_triples.jsonl": ("record_id", ["record_type", "record_id", "action_lemma", "sentence"], True),
    "month1/verbnet_mappings.jsonl": ("action_lemma", ["action_lemma", "has_mapping"], False),
    "month2/framenet_mappings.jsonl": ("action_lemma", ["action_lemma", "has_mapping"], False),
    "month2/srl_roles.jsonl": ("record_id", ["record_type", "record_id", "predicate_lemma", "sentence"], True),
    "month2/diy_actionnet_v1.jsonl": ("action_lemma", ["action_lemma", "cluster_id", "cluster_label"], False),
    "month3/step_clip_scores.jsonl": ("clip_id", ["step_id", "clip_id", "structured_score"], True),
    "month3/pairwise_eval_dense.jsonl": ("comparison_id", ["comparison_id", "winner_clip_id", "model_name"], False),
    "month3/pairwise_eval_structured.jsonl": ("comparison_id", ["comparison_id", "winner_clip_id", "model_name"], False),
    "month3/pairwise_eval_hybrid.jsonl": ("comparison_id", ["comparison_id", "winner_clip_id", "model_name"], False),
}


def verify_output_repository(output_dir: Path) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for relative_path, (id_field, required_fields, allow_duplicate_ids) in REQUIRED_ARTIFACTS.items():
        path = output_dir / relative_path
        if not path.exists():
            raise DataQualityError(f"Missing required artifact: {path}")
        report = validate_jsonl_basic(path, id_field=id_field, required_fields=required_fields)
        if allow_duplicate_ids:
            report_for_failure = dict(report)
            report_for_failure["duplicate_id_count"] = 0
            report_for_failure["duplicate_ids"] = []
            require_nonempty_report(report_for_failure, relative_path)
        else:
            require_nonempty_report(report, relative_path)
        reports[relative_path] = report

    summary_path = output_dir / "month3" / "evaluation_summary.json"
    if not summary_path.exists():
        raise DataQualityError(f"Missing required evaluation summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for model_name in ["dense", "structured", "hybrid"]:
        if model_name not in summary:
            raise DataQualityError(f"Evaluation summary is missing model {model_name!r}")
        if summary[model_name].get("accuracy") is None:
            raise DataQualityError(f"Evaluation summary has no accuracy for {model_name!r}")
    reports["month3/evaluation_summary.json"] = summary

    report_path = output_dir / "verification_report.json"
    report_path.write_text(json.dumps(reports, indent=2, sort_keys=True), encoding="utf-8")
    return reports

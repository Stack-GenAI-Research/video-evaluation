import csv
import json

from action_semantics.io_utils import write_jsonl
from action_semantics.models import ActionTriple, FrameNetMapping, VerbNetMapping
from action_semantics.quality_review import build_quality_review, summarize_manual_review


def test_build_quality_review_writes_summary_and_manual_sample(tmp_path):
    clips_path = tmp_path / "clips.jsonl"
    month1 = tmp_path / "month1"
    month2 = tmp_path / "month2"
    output = tmp_path / "quality"
    month1.mkdir()
    month2.mkdir()
    write_jsonl(
        clips_path,
        [
            {"clip_id": "c1", "title": "Tighten a pipe"},
            {"clip_id": "c2", "title": "No extracted action"},
        ],
    )
    write_jsonl(
        month1 / "action_object_tool_triples.jsonl",
        [
            ActionTriple(
                record_type="clip",
                record_id="c1",
                source_field="title",
                action="tighten",
                action_lemma="tighten",
                action_text="Tighten",
                object_text="pipe",
                object_lemmas=["pipe"],
                context_tool_lemmas=["wrench"],
                sentence="Tighten a pipe.",
                extraction_method="test",
            )
        ],
    )
    write_jsonl(
        month1 / "verbnet_mappings.jsonl",
        [VerbNetMapping(action_lemma="tighten", verbnet_classes=["amalgamate-22.2"], has_mapping=True)],
    )
    write_jsonl(
        month2 / "framenet_mappings.jsonl",
        [FrameNetMapping(action_lemma="tighten", frames=[], has_mapping=False)],
    )

    paths = build_quality_review(
        clips_jsonl=clips_path,
        month1_dir=month1,
        month2_dir=month2,
        output_dir=output,
    )

    summary = json.loads(paths["quality_summary"].read_text(encoding="utf-8"))
    assert summary["clip_action_coverage"] == 0.5
    assert summary["direct_tool_coverage"] == 0.0
    assert summary["record_tool_context_coverage"] == 1.0
    assert summary["verbnet_mapping_coverage"] == 1.0
    assert summary["framenet_mapping_coverage"] == 0.0
    with paths["manual_review"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["review_group"] == "metadata_tool_fallback"
    assert rows[0]["tool_correct"] == ""


def test_summarize_manual_review_uses_only_human_labeled_rows(tmp_path):
    review_path = tmp_path / "review.csv"
    review_path.write_text(
        "review_group,action_correct,object_correct,tool_correct\n"
        "complete_direct,yes,yes,no\n"
        "complete_direct,no,,yes\n",
        encoding="utf-8",
    )

    summary = summarize_manual_review(review_path, tmp_path / "results.json")

    assert summary["overall"]["action_correct"] == {
        "labeled": 2,
        "correct": 1,
        "precision": 0.5,
    }
    assert summary["overall"]["object_correct"]["labeled"] == 1
    assert summary["overall"]["tool_correct"]["precision"] == 0.5

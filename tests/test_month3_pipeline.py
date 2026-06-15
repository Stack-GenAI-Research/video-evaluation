import json

from action_semantics.config import PipelineConfig
from action_semantics.io_utils import write_jsonl
from action_semantics.models import ActionTriple, FrameNetMapping, TaxonomyAssignment, VerbNetMapping
from action_semantics.retrieval.experiments import run_month3


def _triple(record_type: str, record_id: str, action: str, obj: str) -> ActionTriple:
    return ActionTriple(
        record_type=record_type,
        record_id=record_id,
        source_field="description",
        action=action,
        action_lemma=action,
        action_text=action,
        object_text=obj,
        object_lemmas=[obj],
        tool_text="wrench",
        tool_lemmas=["wrench"],
        sentence=f"{action} the {obj} with a wrench.",
        extraction_method="test_fixture",
    )


def test_run_month3_writes_expected_outputs(tmp_path):
    clips_path = tmp_path / "clips.jsonl"
    steps_path = tmp_path / "steps.jsonl"
    pairwise_path = tmp_path / "pairwise.jsonl"
    month1_dir = tmp_path / "outputs" / "month1"
    month2_dir = tmp_path / "outputs" / "month2"
    output_dir = tmp_path / "outputs"
    month1_dir.mkdir(parents=True)
    month2_dir.mkdir(parents=True)

    write_jsonl(
        clips_path,
        [
            {"clip_id": "clip_good", "dense_embeddings": {"description": [1.0, 0.0]}},
            {"clip_id": "clip_bad", "dense_embeddings": {"description": [0.0, 1.0]}},
        ],
    )
    write_jsonl(
        steps_path,
        [{"step_id": "step_1", "dense_embeddings": {"description": [1.0, 0.0]}}],
    )
    write_jsonl(
        pairwise_path,
        [
            {
                "comparison_id": "cmp_1",
                "step_id": "step_1",
                "clip_a_id": "clip_good",
                "clip_b_id": "clip_bad",
                "winner_clip_id": "clip_good",
            }
        ],
    )
    write_jsonl(
        month1_dir / "action_object_tool_triples.jsonl",
        [
            _triple("step", "step_1", "tighten", "pipe"),
            _triple("clip", "clip_good", "tighten", "pipe"),
            _triple("clip", "clip_bad", "paint", "wall"),
        ],
    )
    write_jsonl(
        month1_dir / "verbnet_mappings.jsonl",
        [
            VerbNetMapping(action_lemma="tighten", verbnet_classes=["test-1"], has_mapping=True),
            VerbNetMapping(action_lemma="paint", verbnet_classes=["test-2"], has_mapping=True),
        ],
    )
    write_jsonl(
        month2_dir / "framenet_mappings.jsonl",
        [
            FrameNetMapping(action_lemma="tighten", frames=["attaching"], has_mapping=True),
            FrameNetMapping(action_lemma="paint", frames=["covering"], has_mapping=True),
        ],
    )
    write_jsonl(
        month2_dir / "diy_actionnet_v1.jsonl",
        [
            TaxonomyAssignment(action_lemma="tighten", cluster_id=1, cluster_label="tighten", support_count=2),
            TaxonomyAssignment(action_lemma="paint", cluster_id=2, cluster_label="paint", support_count=1),
        ],
    )

    paths = run_month3(
        clips_jsonl=clips_path,
        steps_jsonl=steps_path,
        pairwise_jsonl=pairwise_path,
        month1_dir=month1_dir,
        month2_dir=month2_dir,
        config=PipelineConfig(output_dir=output_dir),
    )

    assert paths["scores"].exists()
    assert paths["summary"].exists()
    summary = json.loads(paths["summary"].read_text())
    assert summary["dense"]["accuracy"] == 1.0
    assert summary["structured"]["accuracy"] == 1.0
    assert summary["hybrid"]["accuracy"] == 1.0

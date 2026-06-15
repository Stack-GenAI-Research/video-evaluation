from action_semantics.models import ActionTriple
from action_semantics.taxonomy import build_diy_actionnet


def _triple(action: str, record_id: str) -> ActionTriple:
    return ActionTriple(
        record_type="clip",
        record_id=record_id,
        source_field="summary",
        action=action,
        action_lemma=action,
        action_text=action,
        object_text="pipe",
        object_lemmas=["pipe"],
        tool_text="wrench",
        tool_lemmas=["wrench"],
        sentence=f"Use a wrench to {action} the pipe.",
        extraction_method="test",
    )


def test_taxonomy_handles_one_supported_action():
    assignments, diagnostics = build_diy_actionnet([_triple("tighten", "c1")], min_support=1)
    assert len(assignments) == 1
    assert assignments[0].action_lemma == "tighten"
    assert assignments[0].cluster_id == 1
    assert diagnostics["cluster_count"] == 1

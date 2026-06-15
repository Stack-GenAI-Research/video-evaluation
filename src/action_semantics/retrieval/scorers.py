from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from action_semantics.extraction.triples import triples_to_lookup
from action_semantics.models import (
    ActionTriple,
    ClipRecord,
    FrameNetMapping,
    ScoreRow,
    StepRecord,
    TaxonomyAssignment,
    VerbNetMapping,
)
from action_semantics.retrieval.embeddings import mean_dense_score


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = {value for value in left if value}
    right_set = {value for value in right if value}
    if not left_set and not right_set:
        return 0.0
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def max_pairwise_jaccard(left_rows: list[list[str]], right_rows: list[list[str]]) -> float:
    if not left_rows or not right_rows:
        return 0.0
    return max(jaccard(left, right) for left in left_rows for right in right_rows)


@dataclass(frozen=True)
class StructuredResources:
    triples: list[ActionTriple]
    verbnet: list[VerbNetMapping]
    framenet: list[FrameNetMapping]
    taxonomy: list[TaxonomyAssignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "triple_lookup", triples_to_lookup(self.triples))
        object.__setattr__(
            self,
            "verbnet_lookup",
            {row.action_lemma: set(row.verbnet_classes) for row in self.verbnet},
        )
        object.__setattr__(
            self,
            "framenet_lookup",
            {row.action_lemma: set(row.frames) for row in self.framenet},
        )
        object.__setattr__(
            self,
            "taxonomy_lookup",
            {row.action_lemma: int(row.cluster_id) for row in self.taxonomy},
        )

    def triples_for(self, record_type: str, record_id: str) -> list[ActionTriple]:
        return self.triple_lookup.get((record_type, record_id), [])


@dataclass(frozen=True)
class StructuredWeights:
    action: float = 0.30
    verbnet: float = 0.15
    framenet: float = 0.10
    taxonomy: float = 0.15
    object: float = 0.20
    tool: float = 0.10

    def normalized(self) -> "StructuredWeights":
        total = self.action + self.verbnet + self.framenet + self.taxonomy + self.object + self.tool
        if total <= 0:
            raise ValueError("Structured weights must sum to a positive value.")
        return StructuredWeights(
            action=self.action / total,
            verbnet=self.verbnet / total,
            framenet=self.framenet / total,
            taxonomy=self.taxonomy / total,
            object=self.object / total,
            tool=self.tool / total,
        )


def _action_match(step_triples: list[ActionTriple], clip_triples: list[ActionTriple]) -> float:
    return jaccard(
        [triple.action_lemma for triple in step_triples],
        [triple.action_lemma for triple in clip_triples],
    )


def _verbnet_match(
    step_triples: list[ActionTriple],
    clip_triples: list[ActionTriple],
    lookup: dict[str, set[str]],
) -> float:
    left = set().union(*(lookup.get(triple.action_lemma, set()) for triple in step_triples)) if step_triples else set()
    right = set().union(*(lookup.get(triple.action_lemma, set()) for triple in clip_triples)) if clip_triples else set()
    return jaccard(left, right)


def _framenet_match(
    step_triples: list[ActionTriple],
    clip_triples: list[ActionTriple],
    lookup: dict[str, set[str]],
) -> float:
    left = set().union(*(lookup.get(triple.action_lemma, set()) for triple in step_triples)) if step_triples else set()
    right = set().union(*(lookup.get(triple.action_lemma, set()) for triple in clip_triples)) if clip_triples else set()
    return jaccard(left, right)


def _taxonomy_match(
    step_triples: list[ActionTriple],
    clip_triples: list[ActionTriple],
    lookup: dict[str, int],
) -> float:
    left = [str(lookup[triple.action_lemma]) for triple in step_triples if triple.action_lemma in lookup]
    right = [str(lookup[triple.action_lemma]) for triple in clip_triples if triple.action_lemma in lookup]
    return jaccard(left, right)


def structured_score(
    step_id: str,
    clip_id: str,
    resources: StructuredResources,
    weights: StructuredWeights | None = None,
) -> dict[str, float]:
    weights = (weights or StructuredWeights()).normalized()
    step_triples = resources.triples_for("step", step_id)
    clip_triples = resources.triples_for("clip", clip_id)
    object_score = max_pairwise_jaccard(
        [triple.object_lemmas for triple in step_triples],
        [triple.object_lemmas for triple in clip_triples],
    )
    tool_score = max_pairwise_jaccard(
        [triple.tool_lemmas for triple in step_triples],
        [triple.tool_lemmas for triple in clip_triples],
    )
    action_score = _action_match(step_triples, clip_triples)
    verbnet_score = _verbnet_match(step_triples, clip_triples, resources.verbnet_lookup)
    framenet_score = _framenet_match(step_triples, clip_triples, resources.framenet_lookup)
    taxonomy_score = _taxonomy_match(step_triples, clip_triples, resources.taxonomy_lookup)
    total = (
        weights.action * action_score
        + weights.verbnet * verbnet_score
        + weights.framenet * framenet_score
        + weights.taxonomy * taxonomy_score
        + weights.object * object_score
        + weights.tool * tool_score
    )
    return {
        "structured_score": float(total),
        "action_match": float(action_score),
        "verbnet_match": float(verbnet_score),
        "framenet_match": float(framenet_score),
        "taxonomy_match": float(taxonomy_score),
        "object_match": float(object_score),
        "tool_match": float(tool_score),
    }


def score_step_clip(
    step: StepRecord,
    clip: ClipRecord,
    resources: StructuredResources,
    dense_keys: list[str] | None = None,
    hybrid_alpha: float = 0.5,
) -> ScoreRow:
    dense = mean_dense_score(step.dense_embeddings, clip.dense_embeddings, dense_keys)
    structured_parts = structured_score(step.step_id, clip.clip_id, resources)
    structured = structured_parts["structured_score"]
    hybrid = None
    if dense is not None:
        dense_01 = (dense + 1.0) / 2.0
        hybrid = hybrid_alpha * dense_01 + (1.0 - hybrid_alpha) * structured
    return ScoreRow(
        step_id=step.step_id,
        clip_id=clip.clip_id,
        dense_score=dense,
        structured_score=structured,
        hybrid_score=hybrid,
        action_match=structured_parts["action_match"],
        object_match=structured_parts["object_match"],
        tool_match=structured_parts["tool_match"],
        taxonomy_match=structured_parts["taxonomy_match"],
        framenet_match=structured_parts["framenet_match"],
        verbnet_match=structured_parts["verbnet_match"],
    )


def resources_from_files(month1_dir: Any, month2_dir: Any) -> StructuredResources:
    from pathlib import Path

    from action_semantics.io_utils import read_jsonl_model

    m1 = Path(month1_dir)
    m2 = Path(month2_dir)
    return StructuredResources(
        triples=read_jsonl_model(m1 / "action_object_tool_triples.jsonl", ActionTriple),
        verbnet=read_jsonl_model(m1 / "verbnet_mappings.jsonl", VerbNetMapping),
        framenet=read_jsonl_model(m2 / "framenet_mappings.jsonl", FrameNetMapping),
        taxonomy=read_jsonl_model(m2 / "diy_actionnet_v1.jsonl", TaxonomyAssignment),
    )

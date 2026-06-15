from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Token

from action_semantics.models import SrlRole, TextSegment
from action_semantics.text import normalize_term

_AGENT_DEPS = {"nsubj", "agent", "csubj"}
_PATIENT_DEPS = {"dobj", "obj", "attr", "dative", "oprd"}
_SCOPE_PREPS = {"in", "on", "onto", "into", "over", "under", "through", "around", "from", "to"}
_INSTRUMENT_PREPS = {"with", "using", "via", "by"}


@lru_cache(maxsize=4)
def load_model(model_name: str) -> Language:
    try:
        return spacy.load(model_name, disable=["ner"])
    except OSError as exc:
        raise RuntimeError(f"spaCy model {model_name!r} is not installed.") from exc


def _subtree_text(token: Token | None) -> str | None:
    if token is None:
        return None
    tokens = sorted(token.subtree, key=lambda item: item.i)
    text = normalize_term(" ".join(item.text for item in tokens))
    return text or None


def _child_by_dep(verb: Token, deps: set[str]) -> Token | None:
    for child in verb.children:
        if child.dep_ in deps:
            return child
    return None


def _prep_object(verb: Token, prep_lemmas: set[str]) -> Token | None:
    for child in verb.children:
        if child.dep_ == "prep" and child.lemma_.lower() in prep_lemmas:
            for grand in child.children:
                if grand.dep_ in _PATIENT_DEPS or grand.pos_ in {"NOUN", "PROPN", "PRON"}:
                    return grand
    return None


def roles_from_doc(segment: TextSegment, doc: Doc) -> list[SrlRole]:
    rows: list[SrlRole] = []
    for sentence in doc.sents:
        for token in sentence:
            if token.pos_ not in {"VERB", "AUX"}:
                continue
            lemma = normalize_term(token.lemma_ or token.text)
            if not lemma or (lemma in {"be", "have", "do"} and not _child_by_dep(token, _PATIENT_DEPS)):
                continue
            rows.append(
                SrlRole(
                    record_type=segment.record_type,
                    record_id=segment.record_id,
                    source_field=segment.source_field,
                    predicate_lemma=lemma,
                    predicate_text=token.text,
                    agent=_subtree_text(_child_by_dep(token, _AGENT_DEPS)),
                    patient=_subtree_text(_child_by_dep(token, _PATIENT_DEPS)),
                    instrument=_subtree_text(_prep_object(token, _INSTRUMENT_PREPS)),
                    location_or_scope=_subtree_text(_prep_object(token, _SCOPE_PREPS)),
                    sentence=sentence.text.strip(),
                    confidence=0.65,
                )
            )
    return rows


def extract_srl_roles(segments: Iterable[TextSegment], model_name: str) -> list[SrlRole]:
    nlp = load_model(model_name)
    segment_list = list(segments)
    output: list[SrlRole] = []
    docs = nlp.pipe([segment.text for segment in segment_list], batch_size=64)
    for segment, doc in zip(segment_list, docs, strict=True):
        output.extend(roles_from_doc(segment, doc))
    return output


def dependency_srl(segment: TextSegment, model_name: str) -> list[SrlRole]:
    nlp = load_model(model_name)
    return roles_from_doc(segment, nlp(segment.text))

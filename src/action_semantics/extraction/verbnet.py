from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from nltk.corpus import verbnet as vn
from nltk.corpus import wordnet as wn

from action_semantics.models import ActionTriple, VerbNetMapping
from action_semantics.text import normalize_term


@lru_cache(maxsize=4096)
def map_verbnet(action_lemma: str) -> VerbNetMapping:
    lemma = normalize_term(action_lemma)
    classes: list[str] = []
    synsets: list[str] = []
    if lemma:
        try:
            classes = sorted(set(vn.classids(lemma=lemma)))
        except LookupError as exc:
            raise RuntimeError(
                "NLTK VerbNet data is not installed. Run: python -m nltk.downloader verbnet"
            ) from exc
        except Exception:
            classes = []
        try:
            synsets = sorted({syn.name() for syn in wn.synsets(lemma, pos=wn.VERB)})
        except LookupError as exc:
            raise RuntimeError(
                "NLTK WordNet data is not installed. Run: python -m nltk.downloader wordnet omw-1.4"
            ) from exc
    return VerbNetMapping(
        action_lemma=lemma,
        verbnet_classes=classes,
        wordnet_synsets=synsets,
        has_mapping=bool(classes),
    )


def map_triple_verbs(triples: Iterable[ActionTriple]) -> list[VerbNetMapping]:
    lemmas = sorted({triple.action_lemma for triple in triples if triple.action_lemma})
    return [map_verbnet(lemma) for lemma in lemmas]

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

from nltk.corpus import framenet as fn

from action_semantics.models import ActionTriple, FrameNetMapping
from action_semantics.text import normalize_term


@lru_cache(maxsize=4096)
def map_framenet(action_lemma: str) -> FrameNetMapping:
    lemma = normalize_term(action_lemma)
    frames: set[str] = set()
    lexical_units: set[str] = set()
    if lemma:
        pattern = rf"(?i)^{re.escape(lemma)}\.v$"
        try:
            lus = fn.lus(pattern)
        except LookupError as exc:
            raise RuntimeError(
                "NLTK FrameNet data is not installed. Run: python -m nltk.downloader framenet_v17"
            ) from exc
        for lu in lus:
            name = getattr(lu, "name", None) or lu.get("name")
            frame = getattr(lu, "frame", None) or lu.get("frame")
            frame_name = None
            if frame is not None:
                frame_name = getattr(frame, "name", None) or frame.get("name")
            if name:
                lexical_units.add(str(name))
            if frame_name:
                frames.add(str(frame_name))
    return FrameNetMapping(
        action_lemma=lemma,
        frames=sorted(frames),
        lexical_units=sorted(lexical_units),
        has_mapping=bool(frames),
    )


def map_triple_frames(triples: Iterable[ActionTriple]) -> list[FrameNetMapping]:
    lemmas = sorted({triple.action_lemma for triple in triples if triple.action_lemma})
    return [map_framenet(lemma) for lemma in lemmas]

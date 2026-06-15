from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float | None:
    if left is None or right is None:
        return None
    if len(left) == 0 or len(right) == 0 or len(left) != len(right):
        return None
    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    left_norm = np.linalg.norm(left_array)
    right_norm = np.linalg.norm(right_array)
    if left_norm == 0 or right_norm == 0:
        return None
    value = float(np.dot(left_array, right_array) / (left_norm * right_norm))
    if math.isnan(value):
        return None
    return value


def shared_embedding_keys(
    step_embeddings: dict[str, list[float]], clip_embeddings: dict[str, list[float]]
) -> list[str]:
    return sorted(set(step_embeddings) & set(clip_embeddings))


def mean_dense_score(
    step_embeddings: dict[str, list[float]],
    clip_embeddings: dict[str, list[float]],
    requested_keys: Iterable[str] | None = None,
) -> float | None:
    keys = list(requested_keys) if requested_keys is not None else shared_embedding_keys(step_embeddings, clip_embeddings)
    scores = [cosine_similarity(step_embeddings.get(key), clip_embeddings.get(key)) for key in keys]
    valid = [score for score in scores if score is not None]
    if not valid:
        return None
    return float(np.mean(valid))

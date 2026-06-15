from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import Normalizer

from .models import ActionTriple, TaxonomyAssignment
from .text import normalize_term


def load_triples_jsonl(path: Path) -> list[ActionTriple]:
    from .io_utils import read_jsonl_model

    return read_jsonl_model(path, ActionTriple)


def _context_document(action: str, triples: list[ActionTriple]) -> str:
    terms: list[str] = [action] * 6
    for triple in triples:
        terms.extend(triple.object_lemmas)
        terms.extend(triple.tool_lemmas)
        terms.extend(triple.material_lemmas)
        terms.extend(normalize_term(triple.sentence).split())
    return " ".join(term for term in terms if term)


def action_context_table(triples: list[ActionTriple], min_support: int = 2) -> pd.DataFrame:
    by_action: dict[str, list[ActionTriple]] = defaultdict(list)
    for triple in triples:
        if triple.action_lemma:
            by_action[triple.action_lemma].append(triple)
    rows: list[dict[str, Any]] = []
    for action, action_triples in sorted(by_action.items()):
        if len(action_triples) < min_support:
            continue
        objects = Counter(term for triple in action_triples for term in triple.object_lemmas)
        tools = Counter(term for triple in action_triples for term in triple.tool_lemmas)
        materials = Counter(term for triple in action_triples for term in triple.material_lemmas)
        rows.append(
            {
                "action_lemma": action,
                "support_count": len(action_triples),
                "document": _context_document(action, action_triples),
                "top_objects": [term for term, _ in objects.most_common(10)],
                "top_tools": [term for term, _ in tools.most_common(10)],
                "top_materials": [term for term, _ in materials.most_common(10)],
            }
        )
    return pd.DataFrame(rows)


def choose_cluster_count(matrix: np.ndarray, min_clusters: int = 8, max_clusters: int = 80) -> int:
    n_rows = matrix.shape[0]
    if n_rows < 4:
        return max(1, n_rows)
    upper = min(max_clusters, max(2, n_rows - 1))
    lower = min(min_clusters, upper)
    candidates = sorted(set([lower, int(math.sqrt(n_rows)), min(upper, 20), upper]))
    candidates = [value for value in candidates if 2 <= value < n_rows]
    if not candidates:
        return 2
    distance_tree = linkage(matrix, method="ward")
    best_k = candidates[0]
    best_score = -1.0
    for k in candidates:
        labels = fcluster(distance_tree, t=k, criterion="maxclust")
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(matrix, labels)
        if score > best_score:
            best_score = score
            best_k = k
    return best_k


def _cluster_label(actions: list[str], rows: pd.DataFrame) -> str:
    action_part = ", ".join(actions[:3])
    object_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    for _, row in rows.iterrows():
        object_counts.update(row["top_objects"])
        tool_counts.update(row["top_tools"])
    context_terms = [term for term, _ in (object_counts + tool_counts).most_common(2)]
    if context_terms:
        return f"{action_part} / {' + '.join(context_terms)}"
    return action_part


def build_diy_actionnet(
    triples: list[ActionTriple],
    *,
    min_support: int = 2,
    random_seed: int = 1729,
) -> tuple[list[TaxonomyAssignment], dict[str, Any]]:
    table = action_context_table(triples, min_support=min_support)
    if table.empty:
        raise ValueError("No actions met the minimum support threshold for taxonomy clustering.")
    if table.shape[0] == 1:
        row = table.iloc[0]
        assignment = TaxonomyAssignment(
            action_lemma=row["action_lemma"],
            cluster_id=1,
            cluster_label=_cluster_label([row["action_lemma"]], table),
            support_count=int(row["support_count"]),
            representative_objects=list(row["top_objects"]),
            representative_tools=list(row["top_tools"]),
            representative_materials=list(row["top_materials"]),
        )
        diagnostics = {
            "action_count": 1,
            "cluster_count": 1,
            "min_support": min_support,
            "cluster_sizes": {"1": 1},
            "note": "Only one action met the support threshold, so no clustering was needed.",
        }
        return [assignment], diagnostics

    vectorizer = TfidfVectorizer(
        lowercase=True,
        min_df=1,
        max_df=0.95,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    x = vectorizer.fit_transform(table["document"].tolist())
    n_components = min(100, x.shape[0] - 1, x.shape[1] - 1)
    if n_components >= 2:
        svd = TruncatedSVD(n_components=n_components, random_state=random_seed)
        matrix = Normalizer(copy=False).fit_transform(svd.fit_transform(x))
    else:
        matrix = x.toarray()
    if matrix.shape[1] == 0:
        matrix = np.ones((table.shape[0], 1), dtype=float)
    k = choose_cluster_count(np.asarray(matrix))
    if k <= 1:
        labels = np.ones(table.shape[0], dtype=int)
    else:
        labels = fcluster(linkage(matrix, method="ward"), t=k, criterion="maxclust")
    table = table.assign(cluster_id=labels.astype(int))

    assignments: list[TaxonomyAssignment] = []
    for cluster_id, group in table.groupby("cluster_id"):
        actions = group.sort_values(["support_count", "action_lemma"], ascending=[False, True])[
            "action_lemma"
        ].tolist()
        label = _cluster_label(actions, group)
        for _, row in group.iterrows():
            assignments.append(
                TaxonomyAssignment(
                    action_lemma=row["action_lemma"],
                    cluster_id=int(cluster_id),
                    cluster_label=label,
                    support_count=int(row["support_count"]),
                    representative_objects=list(row["top_objects"]),
                    representative_tools=list(row["top_tools"]),
                    representative_materials=list(row["top_materials"]),
                )
            )

    diagnostics = {
        "action_count": int(table.shape[0]),
        "cluster_count": int(len(set(labels))),
        "min_support": min_support,
        "cluster_sizes": {
            str(cluster_id): int(size)
            for cluster_id, size in table.groupby("cluster_id").size().sort_index().items()
        },
    }
    return assignments, diagnostics


def write_taxonomy_artifacts(
    output_dir: Path,
    assignments: list[TaxonomyAssignment],
    diagnostics: dict[str, Any],
) -> dict[str, Path]:
    from .io_utils import write_csv, write_jsonl

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "diy_actionnet_v1.jsonl"
    csv_path = output_dir / "verb_cluster_assignments.csv"
    diagnostics_path = output_dir / "diy_actionnet_diagnostics.json"
    write_jsonl(json_path, assignments)
    write_csv(
        csv_path,
        [row.model_dump(mode="json") for row in assignments],
        fieldnames=list(TaxonomyAssignment.model_fields),
    )
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2, sort_keys=True), encoding="utf-8")
    return {"taxonomy_jsonl": json_path, "taxonomy_csv": csv_path, "diagnostics": diagnostics_path}

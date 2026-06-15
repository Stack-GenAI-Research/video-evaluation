from __future__ import annotations

from pathlib import Path

from .config import PipelineConfig
from .extraction.framenet import map_triple_frames
from .extraction.srl import extract_srl_roles
from .io_utils import read_jsonl_model, write_csv, write_jsonl
from .models import ActionTriple, SrlRole, TextSegment
from .provenance import build_manifest, write_manifest
from .taxonomy import build_diy_actionnet, write_taxonomy_artifacts


def run_month2(
    *,
    month1_dir: Path,
    config: PipelineConfig,
    min_taxonomy_support: int = 2,
) -> dict[str, Path]:
    month_dir = config.ensure_output_dir() / "month2"
    month_dir.mkdir(parents=True, exist_ok=True)

    triples_path = month1_dir / "action_object_tool_triples.jsonl"
    segments_path = month1_dir / "text_segments.jsonl"
    triples = read_jsonl_model(triples_path, ActionTriple)
    segments = read_jsonl_model(segments_path, TextSegment)

    framenet_rows = map_triple_frames(triples)
    srl_rows = extract_srl_roles(segments, config.spacy_model)
    assignments, diagnostics = build_diy_actionnet(
        triples,
        min_support=min_taxonomy_support,
        random_seed=config.random_seed,
    )

    framenet_path = month_dir / "framenet_mappings.jsonl"
    srl_path = month_dir / "srl_roles.jsonl"
    srl_csv_path = month_dir / "srl_roles.csv"
    write_jsonl(framenet_path, framenet_rows)
    write_jsonl(srl_path, srl_rows)
    write_csv(
        srl_csv_path,
        [row.model_dump(mode="json") for row in srl_rows],
        fieldnames=list(SrlRole.model_fields),
    )
    taxonomy_paths = write_taxonomy_artifacts(month_dir, assignments, diagnostics)

    output_files = [framenet_path, srl_path, srl_csv_path, *taxonomy_paths.values()]
    manifest_path = month_dir / "manifest.json"
    write_manifest(
        manifest_path,
        build_manifest(
            command="run-month2",
            input_files=[triples_path, segments_path],
            output_files=output_files,
            parameters={
                "spacy_model": config.spacy_model,
                "min_taxonomy_support": min_taxonomy_support,
                "random_seed": config.random_seed,
            },
        ),
    )
    return {
        "month_dir": month_dir,
        "framenet": framenet_path,
        "srl": srl_path,
        "srl_csv": srl_csv_path,
        "manifest": manifest_path,
        **taxonomy_paths,
    }

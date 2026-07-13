import json
from pathlib import Path

from action_semantics import index_freshness
from action_semantics.io_utils import sha256_file


def _manifest(source: Path, artifact: Path, parameters: dict) -> dict:
    return {
        "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
        "outputs": [{"path": str(artifact), "sha256": sha256_file(artifact)}],
        "parameters": parameters,
    }


def test_index_freshness_checks_source_code_versions_and_artifact_hashes(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text('{"video": 1}\n', encoding="utf-8")
    output_dir = tmp_path / "index"
    output_dir.mkdir()
    artifact = output_dir / "clips.jsonl"
    artifact.write_text('{"clip": 1}\n', encoding="utf-8")
    monkeypatch.setattr(index_freshness, "index_build_code_sha256", lambda: "code-v1")
    monkeypatch.setattr(
        index_freshness,
        "_installed_version",
        lambda name: {"spacy": "3.8.14", "en-core-web-sm": "3.8.0"}.get(name),
    )
    parameters = index_freshness.index_build_versions("en_core_web_sm")
    manifest_path = output_dir / "index_manifest.json"
    manifest_path.write_text(
        json.dumps(_manifest(source, artifact, parameters)), encoding="utf-8"
    )

    assert index_freshness.index_staleness_reasons(
        source_jsonl=source,
        output_dir=output_dir,
        spacy_model="en_core_web_sm",
    ) == []

    artifact.write_text('{"clip": 2}\n', encoding="utf-8")
    reasons = index_freshness.index_staleness_reasons(
        source_jsonl=source,
        output_dir=output_dir,
        spacy_model="en_core_web_sm",
    )
    assert any("artifact hash changed" in reason for reason in reasons)

    artifact.write_text('{"clip": 1}\n', encoding="utf-8")
    monkeypatch.setattr(index_freshness, "index_build_code_sha256", lambda: "code-v2")
    reasons = index_freshness.index_staleness_reasons(
        source_jsonl=source,
        output_dir=output_dir,
        spacy_model="en_core_web_sm",
    )
    assert any("index_build_code_sha256 changed" in reason for reason in reasons)

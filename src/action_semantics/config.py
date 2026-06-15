from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_SPACY_MODEL = "en_core_web_sm"
DEFAULT_RANDOM_SEED = 1729


@dataclass(frozen=True)
class PipelineConfig:
    output_dir: Path
    spacy_model: str = DEFAULT_SPACY_MODEL
    random_seed: int = DEFAULT_RANDOM_SEED
    min_text_length: int = 3
    clip_limit: int | None = None

    def ensure_output_dir(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir

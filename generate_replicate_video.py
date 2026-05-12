"""
Generate an instructional DIY clip with a Replicate-hosted video model.

Docs used when this script was written:
https://replicate.com/docs/get-started/python
https://replicate.com/collections/text-to-video

Before running:
    pip install replicate
    export REPLICATE_API_TOKEN="..."

Example with a Kling model slug from Replicate:
    python generate_replicate_video.py \
      --model "kwaivgi/kling-v3-video" \
      --prompt "Realistic close-up instructional DIY video: add air to a tire while watching the gauge." \
      --out outputs/replicate_kling.mp4

Important: input schemas differ by model. This script uses common fields and lets you pass
additional JSON with --extra-input '{"duration": 10, "aspect_ratio": "16:9"}'. Check the model's
API tab on Replicate before large batch runs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import replicate


def _save_output(output: Any, out_path: Path) -> None:
    """Save a Replicate file output, list of outputs, URL string, or JSON fallback."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    first = output[0] if isinstance(output, list) and output else output

    if hasattr(first, "read"):
        out_path.write_bytes(first.read())
        return

    if isinstance(first, str) and first.startswith("http"):
        # For URL outputs, write the URL instead of downloading so the script has no requests dependency.
        url_file = out_path.with_suffix(".url.txt")
        url_file.write_text(first, encoding="utf-8")
        print(f"Model returned a URL. Wrote URL to {url_file}")
        return

    out_path.with_suffix(".json").write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")


def generate_video(
    prompt: str,
    out_path: str | Path,
    model: str = "kwaivgi/kling-v3-video",
    extra_input_json: str = "{}",
) -> None:
    out_path = Path(out_path)
    extra_input = json.loads(extra_input_json)
    if not isinstance(extra_input, dict):
        raise ValueError("--extra-input must be a JSON object")

    model_input = {"prompt": prompt, **extra_input}
    print(f"Running Replicate model {model} with input keys: {sorted(model_input)}")
    output = replicate.run(model, input=model_input)
    _save_output(output, out_path)
    print(f"Saved Replicate output to {out_path} or sidecar file.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one DIY instructional clip with a Replicate video model.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", default="outputs/replicate_video.mp4")
    parser.add_argument("--model", default="kwaivgi/kling-v3-video")
    parser.add_argument("--extra-input", default="{}", help="JSON object merged into model input")
    args = parser.parse_args()
    generate_video(args.prompt, args.out, args.model, args.extra_input)


if __name__ == "__main__":
    main()

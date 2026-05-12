"""
Generate an instructional DIY clip using Google Veo through the Gemini API.

Docs used when this script was written:
https://ai.google.dev/gemini-api/docs/video

Before running:
    pip install google-genai
    export GOOGLE_API_KEY="..."

Example:
    python generate_google_veo.py \
      --prompt "Realistic close-up instructional DIY video: tighten a compression nut on a toilet fill valve." \
      --out outputs/veo_toilet_fill_valve.mp4
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from google import genai
from google.genai import types


def generate_video(
    prompt: str,
    out_path: str | Path,
    model: str = "veo-3.1-generate-preview",
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    poll_seconds: int = 10,
) -> None:
    client = genai.Client()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    config = types.GenerateVideosConfig(
        resolution=resolution,
        aspect_ratio=aspect_ratio,
    )
    operation = client.models.generate_videos(
        model=model,
        prompt=prompt,
        config=config,
    )
    print(f"Started Gemini/Veo video operation: {operation.name}")

    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(poll_seconds)
        operation = client.operations.get(operation)

    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)
    generated_video.video.save(str(out_path))
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one DIY instructional clip with Google Veo.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", default="outputs/google_veo_video.mp4")
    parser.add_argument("--model", default="veo-3.1-generate-preview")
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args()
    generate_video(args.prompt, args.out, args.model, args.resolution, args.aspect_ratio, args.poll_seconds)


if __name__ == "__main__":
    main()

"""
Generate an instructional DIY clip using the OpenAI Videos API / Sora models.

Docs used when this script was written:
https://developers.openai.com/api/docs/guides/video-generation

Before running:
    pip install openai
    export OPENAI_API_KEY="..."

Example:
    python generate_openai_sora.py \
      --prompt "Realistic close-up instructional DIY video: wrap PTFE tape clockwise on shower-arm threads." \
      --out outputs/sora_ptfe_tape.mp4
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from openai import OpenAI


def generate_video(
    prompt: str,
    out_path: str | Path,
    model: str = "sora-2-pro",
    size: str = "1280x720",
    seconds: str = "8",
    poll_seconds: int = 10,
) -> None:
    client = OpenAI()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    video = client.videos.create(
        model=model,
        prompt=prompt,
        size=size,
        seconds=seconds,
    )
    print(f"Started OpenAI video job: {video.id} status={video.status}")

    while video.status in {"queued", "in_progress"}:
        progress = getattr(video, "progress", None)
        if progress is not None:
            sys.stdout.write(f"\rstatus={video.status} progress={progress:.1f}%")
        else:
            sys.stdout.write(f"\rstatus={video.status}")
        sys.stdout.flush()
        time.sleep(poll_seconds)
        video = client.videos.retrieve(video.id)

    print()
    if video.status != "completed":
        error = getattr(video, "error", None)
        raise RuntimeError(f"OpenAI video generation failed: status={video.status} error={error}")

    content = client.videos.download_content(video.id, variant="video")
    content.write_to_file(str(out_path))
    print(f"Saved {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one DIY instructional clip with OpenAI Sora.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", default="outputs/openai_sora_video.mp4")
    parser.add_argument("--model", default="sora-2-pro")
    parser.add_argument("--size", default="1280x720")
    parser.add_argument("--seconds", default="8")
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args()
    generate_video(args.prompt, args.out, args.model, args.size, args.seconds, args.poll_seconds)


if __name__ == "__main__":
    main()

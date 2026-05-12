"""
Generate an instructional DIY clip using Runway's Python SDK.

Docs used when this script was written:
https://docs.dev.runwayml.com/guides/using-the-api/
https://docs.dev.runwayml.com/api-details/sdks/

Before running:
    pip install runwayml
    export RUNWAYML_API_SECRET="..."

Example:
    python generate_runway.py \
      --prompt "Realistic close-up instructional DIY video: drill a pilot hole perpendicular to a pine board." \
      --out outputs/runway_pilot_hole.txt

Runway returns a URL for generated output. This script writes the URL(s) to the output file.
Use --prompt-image with a public image URL or data URI for image-to-video.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from runwayml import RunwayML, TaskFailedError


def generate_video(
    prompt: str,
    out_path: str | Path,
    model: str = "gen4.5",
    ratio: str = "1280:720",
    duration: int = 5,
    prompt_image: str | None = None,
) -> None:
    client = RunwayML()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs = {
        "model": model,
        "prompt_text": prompt,
        "ratio": ratio,
        "duration": duration,
    }
    if prompt_image:
        kwargs["prompt_image"] = prompt_image

    try:
        task = client.image_to_video.create(**kwargs).wait_for_task_output()
    except TaskFailedError as exc:
        raise RuntimeError(f"Runway generation failed: {exc.task_details}") from exc

    outputs = getattr(task, "output", []) or []
    out_path.write_text("\n".join(outputs), encoding="utf-8")
    print(f"Task complete. Wrote output URL(s) to {out_path}")
    for url in outputs:
        print(url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one DIY instructional clip with Runway.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--out", default="outputs/runway_output_urls.txt")
    parser.add_argument("--model", default="gen4.5")
    parser.add_argument("--ratio", default="1280:720")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--prompt-image", default=None)
    args = parser.parse_args()
    generate_video(args.prompt, args.out, args.model, args.ratio, args.duration, args.prompt_image)


if __name__ == "__main__":
    main()

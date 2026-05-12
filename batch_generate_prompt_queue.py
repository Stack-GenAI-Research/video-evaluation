"""
Create a prompt queue CSV from Stesso-like step metadata.

This script does not call a video API. It converts a step CSV into prompt text that you can
feed into the provider-specific scripts or review before a paid generation batch.

Example:
    python batch_generate_prompt_queue.py --steps sample_steps.csv --architecture structured --out prompt_queue.csv
"""
from __future__ import annotations

import argparse

from video_prompt_utils import load_steps_csv, write_prompt_queue


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a prompt queue CSV for Project 4 video generation.")
    parser.add_argument("--steps", required=True, help="CSV with step_id, domain, step_description, tool_names, supplies_objects")
    parser.add_argument("--architecture", default="structured", choices=["direct", "structured", "metadata", "reference", "sequential", "constraints"])
    parser.add_argument("--duration-seconds", type=int, default=8)
    parser.add_argument("--out", default="prompt_queue.csv")
    args = parser.parse_args()
    steps = load_steps_csv(args.steps)
    write_prompt_queue(steps, args.out, args.architecture, args.duration_seconds)
    print(f"Wrote {len(steps)} prompts to {args.out}")


if __name__ == "__main__":
    main()

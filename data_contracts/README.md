# Data contracts

This folder describes the JSONL files that the Python pipeline expects. Each JSONL file should have one JSON object per line. The schemas only require the stable fields that the code needs, but they allow extra fields so the real Stesso export can keep additional metadata.

### `clips.schema.json`

This schema describes `clips.jsonl`. Each row represents one indexed video clip. The required field is `clip_id`. The row can also include project and video IDs, title, description, summary, transcript fields, `gemini_metadata`, timestamps, and dense embedding arrays.

### `steps.schema.json`

This schema describes `steps.jsonl`. Each row represents one project step. The required field is `step_id`. The row can also include project ID, step index, title, description, tools, materials, techniques, and dense embeddings.

### `pairwise.schema.json`

This schema describes `pairwise.jsonl`. Each row represents one human or model comparison between two clips for the same step. The required fields are `comparison_id`, `step_id`, `clip_a_id`, `clip_b_id`, and `winner_clip_id`.

The join fields should stay exactly the same across files. In particular, do not rename or anonymize `clip_id`, `step_id`, `clip_a_id`, `clip_b_id`, or `winner_clip_id` if the goal is to reproduce the pairwise evaluation.

Extra fields are allowed in all three schemas. This is useful because the export can preserve original Stesso metadata even if the current Python code does not use every field yet.

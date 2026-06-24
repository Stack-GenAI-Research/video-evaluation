# Project 1: Action Semantics for Instructional Video Retrieval

This is my implementation for Project 1 from the Stesso/Purdue research list. The question behind the project is fairly simple: when someone searches for an instructional video, is it enough that a clip is about the same topic, or does it need to show the exact action on the right object with the right tool?

Dense embeddings are good at finding things that are generally related. They can still confuse “same topic” with “same action.” For example, two plumbing clips can be very similar even if one installs a valve and the other removes a pipe. This project tests whether structured action information can make that distinction more directly.

The code extracts action-object-tool-material triples, then adds VerbNet, FrameNet, SRL-style roles, and a first DIY action taxonomy. Once the full research exports are available, it compares dense-only, structured-only, and hybrid retrieval against human pairwise judgments.

## What I accomplished

I added an automated path for the private `indexed-videos-250.jsonl` sample. This file is not shaped like the main pipeline input: it contains 250 videos, each with a nested list of clips. The new adapter flattens those nested records into 1,703 stable clip records, keeps the source video and timing information, and writes a profile showing which fields are actually available.

I also added a single Bash script that can set up the environment, run the tests, and run the available pipeline. The script uses a supported Python version, downloads the NLP resources, verifies the code, runs the real sample, and points to the final report.

The important design choice is that the sample pipeline does not invent missing research inputs. It runs Months 1 and 2, which the sample supports, then stops before Month 3. The sample does not contain project steps, `ClipPairComparison` labels, or dense embedding vectors, so a retrieval accuracy number would not be a real result.

## Quick start

On macOS or Linux, from the repository root, run:

```bash
./scripts/run_local_pipeline.sh all
```

This is the normal command to use. It will:

1. Create `.venv` with Python 3.11, 3.12, or 3.13.
2. Install the project and development dependencies.
3. Download spaCy and NLTK resources.
4. Compile the source files, run the test suite, run Ruff, and check the command-line interface.
5. Flatten the private IndexedVideo sample and run its Month 1/2 analysis.
6. Verify the generated artifacts.

The default local output folder is `project1_outputs/indexed-video-sample/`. It is ignored by Git because it contains derived private-data results. The main report is:

```text
project1_outputs/indexed-video-sample/sample_analysis_report.json
```

If the sample JSONL lives somewhere else, point the script at it:

```bash
SAMPLE_JSONL=/secure/path/indexed-videos-250.jsonl \
  ./scripts/run_local_pipeline.sh all
```

The script also supports smaller commands:

```bash
./scripts/run_local_pipeline.sh setup   # install only
./scripts/run_local_pipeline.sh test    # compile, test, lint, and check the CLI
./scripts/run_local_pipeline.sh sample  # run only the real IndexedVideo sample
./scripts/run_local_pipeline.sh --help
```

## Findings from the real sample run

I ran the sample pipeline in June 2026 with `--min-taxonomy-support 2`. The input had 250 videos and 1,703 nested clips. The data is reasonably rich in clip tools (74.5% of clips have a tool field), but less consistent in written descriptions (36.2%) and explicit goals (29.5%).

Month 1 produced 8,823 action triples from 1,006 unique action lemmas. The system extracted an object for 63.1% of the triples. It extracted a dependency-linked tool for only 3.5% of them.

Month 2 produced 1,006 VerbNet mappings, 1,006 FrameNet mappings, 8,823 SRL-style role rows, and a first `DIY-ActionNet` taxonomy with 660 actions in 80 clusters.

These are real extraction results, but they are not retrieval results. I cannot yet say that structured action matching beats dense embeddings, because the sample has no project-step queries, no pairwise human judgments, and no dense vectors to compare against.

The most useful finding so far is the low tool-linkage rate. The source sample often lists a tool as metadata instead of placing it in a sentence such as “tighten the screw with a screwdriver.” That is a concrete error-analysis target: I need to check whether the tool is present but linguistically disconnected from the action, or whether the parser is missing the relationship.

## What the pipeline does

Month 1 converts clip and step text into text segments, extracts action-object-tool-material triples with spaCy dependency parsing, and maps action lemmas to VerbNet and WordNet.

Month 2 maps the actions to FrameNet, extracts dependency-based SRL-style roles, and clusters recurring action contexts into `DIY-ActionNet v1`.

Month 3 is the actual retrieval experiment. It calculates dense, structured, and hybrid scores for each step/clip pair, then compares the predicted winner against the pairwise human label. It reports pairwise accuracy and a bootstrap confidence interval.

The IndexedVideo sample runs only Months 1 and 2. The full path remains in the repository and becomes runnable once the missing exports are available.

## Running the full evaluation later

The full study needs three real JSONL exports:

- `clips.jsonl`: one row per indexed clip, including `clip_id` and any available text and dense embeddings.
- `steps.jsonl`: one row per project step, including `step_id`, text, tools, materials, techniques, and dense embeddings.
- `pairwise.jsonl`: one row per comparison, including `comparison_id`, `step_id`, `clip_a_id`, `clip_b_id`, and `winner_clip_id`.

When those files are available, the same script can validate and run the complete evaluation:

```bash
CLIPS_JSONL=/secure/path/clips.jsonl \
STEPS_JSONL=/secure/path/steps.jsonl \
PAIRWISE_JSONL=/secure/path/pairwise.jsonl \
PROJECT_OUTPUT_DIR=/secure/path/project1_outputs \
  ./scripts/run_local_pipeline.sh full
```

The `full` command validates all three inputs first. It then runs Months 1–3, including output verification. It uses all exported clips (`--clip-limit 0`), so I would first test the command on a smaller secure export before running the full 67K-clip job.

For a more manual workflow, the CLI remains available:

```bash
.venv/bin/action-semantics --help
```

The JSON schemas are in `data_contracts/`, and the PostgreSQL export patterns are in `sql/postgres_export_contract.sql`. The SQL file is a guide, not a production command: table and column names still need to be checked against the real Stesso schema.

## Outputs to inspect

The sample runner writes these files under its output directory:

- `input/indexed_video_clips.jsonl`: the flattened, source-derived clip records.
- `input/indexed_video_profile.json`: record counts, field coverage, and the explicit Month 3 blockers.
- `month1/action_object_tool_triples.csv`: an easy file to inspect for extraction errors.
- `month1/month1_summary.json`: action counts and object/tool coverage.
- `month2/srl_roles.csv`: extracted predicate, patient, instrument, and scope fields.
- `month2/diy_actionnet_v1.jsonl`: the first action taxonomy assignments.
- `sample_analysis_report.json`: the combined result summary.
- `structured_analysis_verification_report.json`: the nonempty-field and artifact checks.

## What still needs to happen

The remaining work is not just “run more code.” I still need the real project-step export, the pairwise comparison export, and dense embeddings before testing the main research hypothesis. I also need a manual, stratified review of triples and SRL rows, especially for actions with tools. After that, I can run the complete dense-versus-structured comparison and make claims about retrieval quality.

For the current detailed data status and exact local verification record, see [DATA_COMPLETION_STATUS.md](DATA_COMPLETION_STATUS.md) and [LOCAL_VERIFICATION.md](LOCAL_VERIFICATION.md).

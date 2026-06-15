# Project 1: Action Semantics for Instructional Video Retrieval

This repository contains the Python code I have written so far for Project 1 from the Stesso/Purdue research project list. The project studies whether structured action information can improve instructional video retrieval. The main idea is to compare dense embedding similarity with action matching, where the code tries to identify the action, object, tool, material, VerbNet class, FrameNet frame, and a first version of a DIY-specific action taxonomy.

The code is written so it can run on the real Stesso export files, but the private Stesso data is not included in this repository. I did not add fake clip rows, fake embeddings, fake pairwise labels, or fake final results. The project PDF says the real study uses the 67K `IndexedVideoClip` records, `geminiMetaData`, transcripts, and 2,077 `ClipPairComparison` rows. Those actual database rows still have to be exported before the full research results can be produced.

### Current project status

The code for the first three months is implemented and can be run after the real JSONL export files are available.

Month 1 is responsible for creating text segments from clips and steps, extracting action-object-tool triples, and mapping action lemmas to VerbNet and WordNet. Month 2 adds FrameNet mappings, dependency-based SRL-style roles, and a first version of `DIY-ActionNet`. Month 3 compares dense, structured, and hybrid scores against the pairwise comparison labels.

The repository also includes input validation, manifest files, output verification, and unit tests for the pieces that can be tested without the private database.

What is finished:

- Text normalization for clip and step fields.
- Text extraction from nested `gemini_metadata` fields.
- Action-object-tool-material triple extraction with spaCy dependency parsing.
- VerbNet and WordNet action mapping through NLTK.
- FrameNet action mapping through NLTK.
- Dependency-based SRL-style extraction for agent, patient, instrument, and location/scope.
- `DIY-ActionNet v1` clustering from extracted action contexts.
- Dense score calculation from shared embedding keys.
- Structured score calculation from action, object, tool, VerbNet, FrameNet, and taxonomy matches.
- Hybrid scoring that combines dense and structured scores.
- Pairwise evaluation against `ClipPairComparison`-style labels.
- Repository verification for the generated month 1, month 2, and month 3 outputs.

What still needs to be completed with the real project data:

- Export the real `clips.jsonl`, `steps.jsonl`, and `pairwise.jsonl` files from PostgreSQL.
- Confirm the real table and column names against the TypeScript models before running the SQL patterns.
- Make sure all required dense embeddings are exported into `dense_embeddings` fields.
- Run the full month 1 through month 3 pipeline on the real export files.
- Review a sample of extracted triples and SRL roles by hand, because extraction quality is part of the research work.
- Check the final retrieval results and write the real research tables only after the real output files are produced.

### Running the Python project

Clone or unzip this repository on a machine with Python 3.11, 3.12, or 3.13. Then, move into the repository directory.

```bash
cd project1-action-semantics
```

Create and activate a virtual environment.

```bash
python -m venv .venv
. .venv/bin/activate
```

On Windows PowerShell, the activation command is different.

```powershell
.venv\Scripts\Activate.ps1
```

Upgrade pip and install the project.

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Install the NLP resources used by month 1 and month 2.

```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader verbnet wordnet omw-1.4 framenet_v17
```

If the machine cannot download these resources, the pipeline will still install, but month 1 and month 2 will stop with an error explaining which resource is missing. That is better than silently producing weak extraction output.

Check that the command line tool is available.

```bash
action-semantics --help
```

The same help command can also be run without installing the console script.

```bash
PYTHONPATH=src python -m action_semantics.cli --help
```

### Running the tests

The repository includes unit tests that do not use the private Stesso dataset.

```bash
python -m pytest -q
```

To also check that all Python files compile, run:

```bash
python -m compileall -q src tests
```

These checks confirm that the package imports, the main utility functions work, and the CLI can be called. They do not replace the full pipeline run on the real 67K clip export.

### Input files needed for the full pipeline

The full pipeline expects three JSONL files. Each line should be one JSON object.

`clips.jsonl` contains one row per indexed video clip. The most important field is `clip_id`. The row can also include title, description, summary, transcript fields, `gemini_metadata`, and dense embeddings.

`steps.jsonl` contains one row per project step. The most important field is `step_id`. The row can also include title, description, tools, materials, techniques, and dense embeddings.

`pairwise.jsonl` contains the pairwise comparison labels. It needs `comparison_id`, `step_id`, `clip_a_id`, `clip_b_id`, and `winner_clip_id`.

The schemas are in `data_contracts/`. Extra fields are allowed, so the export can keep useful original metadata from Stesso.

The ID fields should not be renamed or anonymized if the goal is to reproduce the evaluation. Month 3 depends on exact joins between `step_id`, `clip_id`, `clip_a_id`, `clip_b_id`, and `winner_clip_id`.

### Validating the real exports

Before running extraction, validate the three input files.

```bash
action-semantics validate-inputs \
  --clips-jsonl /secure/path/clips.jsonl \
  --steps-jsonl /secure/path/steps.jsonl \
  --pairwise-jsonl /secure/path/pairwise.jsonl \
  --output-dir /secure/path/project1_outputs
```

This command checks that the files are nonempty, required fields are present, and IDs are not duplicated where they need to be unique.

### Running month 1

Month 1 reads the real clips and steps, builds text segments, extracts action-object-tool triples, and maps actions to VerbNet and WordNet.

```bash
action-semantics run-month1 \
  --clips-jsonl /secure/path/clips.jsonl \
  --steps-jsonl /secure/path/steps.jsonl \
  --output-dir /secure/path/project1_outputs \
  --clip-limit 5000
```

The default clip limit is 5,000 because that matches the month 1 milestone. To run all clips from the CLI, pass `--clip-limit 0` after confirming the compute time is acceptable. For normal project work, I would keep the 5,000 clip run first and only scale up after checking the extraction output.

Month 1 writes:

- `month1/text_segments.jsonl`
- `month1/action_object_tool_triples.jsonl`
- `month1/action_object_tool_triples.csv`
- `month1/verbnet_mappings.jsonl`
- `month1/month1_summary.json`
- `month1/manifest.json`

### Running month 2

Month 2 reads the month 1 outputs, maps actions to FrameNet, extracts SRL-style roles, and builds `DIY-ActionNet v1`.

```bash
action-semantics run-month2 \
  --month1-dir /secure/path/project1_outputs/month1 \
  --output-dir /secure/path/project1_outputs \
  --min-taxonomy-support 2
```

The `--min-taxonomy-support` value controls how many times an action lemma must appear before it is included in the taxonomy clustering. A value of 2 is a reasonable first pass, but it should be tuned after seeing the real action distribution.

Month 2 writes:

- `month2/framenet_mappings.jsonl`
- `month2/srl_roles.jsonl`
- `month2/srl_roles.csv`
- `month2/diy_actionnet_v1.jsonl`
- `month2/verb_cluster_assignments.csv`
- `month2/diy_actionnet_diagnostics.json`
- `month2/manifest.json`

### Running month 3

Month 3 reads the original exports plus the month 1 and month 2 outputs. It scores the clip pairs that appear in the pairwise comparison file and evaluates dense, structured, and hybrid scoring.

```bash
action-semantics run-month3 \
  --clips-jsonl /secure/path/clips.jsonl \
  --steps-jsonl /secure/path/steps.jsonl \
  --pairwise-jsonl /secure/path/pairwise.jsonl \
  --month1-dir /secure/path/project1_outputs/month1 \
  --month2-dir /secure/path/project1_outputs/month2 \
  --output-dir /secure/path/project1_outputs \
  --hybrid-alpha 0.5
```

`--hybrid-alpha` controls how much the hybrid score trusts dense embeddings. A value of `0.5` gives equal weight to the dense and structured scores after the dense score is converted from cosine similarity into a 0 to 1 scale.

If the export has many dense embedding fields and only some should be used, pass the desired keys like this:

```bash
action-semantics run-month3 \
  --clips-jsonl /secure/path/clips.jsonl \
  --steps-jsonl /secure/path/steps.jsonl \
  --pairwise-jsonl /secure/path/pairwise.jsonl \
  --month1-dir /secure/path/project1_outputs/month1 \
  --month2-dir /secure/path/project1_outputs/month2 \
  --output-dir /secure/path/project1_outputs \
  --dense-key title \
  --dense-key description \
  --hybrid-alpha 0.5
```

Month 3 writes:

- `month3/step_clip_scores.jsonl`
- `month3/step_clip_scores.csv`
- `month3/pairwise_eval_dense.jsonl`
- `month3/pairwise_eval_structured.jsonl`
- `month3/pairwise_eval_hybrid.jsonl`
- `month3/evaluation_summary.json`
- `month3/manifest.json`

### Running everything together

After validating the input files, the whole sequence can be run with one command.

```bash
action-semantics run-all \
  --clips-jsonl /secure/path/clips.jsonl \
  --steps-jsonl /secure/path/steps.jsonl \
  --pairwise-jsonl /secure/path/pairwise.jsonl \
  --output-dir /secure/path/project1_outputs \
  --clip-limit 5000 \
  --min-taxonomy-support 2 \
  --hybrid-alpha 0.5
```

This command runs month 1, month 2, month 3, and then checks that the required output artifacts exist.

### Verifying generated outputs

After the pipeline runs, verify the generated output folder.

```bash
action-semantics verify-repository \
  --output-dir /secure/path/project1_outputs
```

The verification step checks that expected files are present, JSONL files are nonempty, required fields are present, and unique IDs are not duplicated where uniqueness is expected. It writes `verification_report.json` into the output directory.

### Exporting from PostgreSQL

The file `sql/postgres_export_contract.sql` contains export patterns for clips, steps, and pairwise comparisons. It is not meant to be copied blindly into production. The table and column names should first be checked against the real Stesso schema and the TypeScript model files named in the project PDF.

The SQL guide also does not contain database credentials. Use the normal secure database connection process outside the repository.

### Package outline

### `action_semantics.cli`

Functionality:
This file defines the command line interface for the project. It includes commands for validating inputs, running month 1, running month 2, running month 3, running all months together, and verifying generated outputs.

Testing:
The help command has been checked locally. Full CLI testing should be done with a small private export that has the same schema as the real files.

Relationship to other files:
The CLI calls `month1.py`, `month2.py`, `retrieval/experiments.py`, and `verification.py`.

### `action_semantics.models`

Functionality:
This file stores the Pydantic models used by the project. These models validate clips, steps, pairwise comparisons, extracted triples, VerbNet mappings, FrameNet mappings, SRL roles, taxonomy assignments, score rows, and pairwise evaluation rows.

Testing:
The models run whenever JSONL files are loaded. If an ID is blank, or if a pairwise winner is not either clip A or clip B, validation fails before scoring starts.

Relationship to other files:
Most other files import one or more models from here.

### `action_semantics.text`

Functionality:
This file normalizes text and converts clip and step records into text segments. It also searches through nested `gemini_metadata` values so useful text in frames, tools, materials, techniques, and summaries can still be used.

Testing:
The current tests check whitespace cleanup and term normalization. More tests should be added after real metadata examples are available.

Relationship to other files:
Month 1 uses this file before running extraction.

### `action_semantics.extraction.triples`

Functionality:
This file uses spaCy dependency parses to extract action-object-tool-material triples from text segments. This is the main month 1 extraction module.

Testing:
The next useful test would use a small private set of real Stesso metadata snippets. That would let us check whether actions like `caulk`, `grout`, `cut`, `remove`, `install`, `tighten`, and `deburr` are attached to the right objects and tools.

Relationship to other files:
Month 1 calls this module, and month 3 uses the extracted triples for structured scoring.

### `action_semantics.extraction.verbnet`

Functionality:
This file maps action lemmas to VerbNet classes and WordNet synsets using NLTK.

Testing:
The main setup issue is missing NLTK data. If the data is missing, the code gives the downloader command instead of failing silently.

Relationship to other files:
Month 1 writes the VerbNet mappings. Month 3 uses them as part of the structured score.

### `action_semantics.extraction.framenet`

Functionality:
This file maps action lemmas to FrameNet lexical units and frames. It is part of the month 2 work.

Testing:
The mapping should be reviewed on real DIY verbs, because many home improvement verbs may not be covered well by general FrameNet resources.

Relationship to other files:
Month 2 writes the FrameNet mappings. Month 3 uses them as another structured scoring signal.

### `action_semantics.extraction.srl`

Functionality:
This file extracts SRL-style roles from dependency parses. It is not a full neural SRL model, but it gives useful fields for agent, patient, instrument, and location/scope.

Testing:
This should be checked against real clip and step text before using the output for research claims.

Relationship to other files:
Month 2 writes the SRL role file for analysis and error review.

### `action_semantics.taxonomy`

Functionality:
This file builds `DIY-ActionNet v1` by grouping extracted action lemmas based on their surrounding object, tool, material, and sentence context.

Testing:
The unit tests check that the taxonomy builder handles a small one-action case. Larger validation needs the real extracted action distribution.

Relationship to other files:
Month 2 calls this file, and month 3 uses the taxonomy assignments in structured scoring.

### `action_semantics.retrieval.scorers`

Functionality:
This file calculates dense scores, structured scores, and hybrid scores for step-clip pairs.

Testing:
The scoring logic should be reviewed with real examples where the correct action matters more than the general topic.

Relationship to other files:
Month 3 calls this file to generate `step_clip_scores.jsonl`.

### `action_semantics.retrieval.evaluation`

Functionality:
This file turns pairwise scores into predicted winners and calculates accuracy with a bootstrap confidence interval. Missing scores are kept as missing data instead of being treated as real ties.

Testing:
The tests check winner prediction, ties, missing scores, reciprocal rank, and NDCG.

Relationship to other files:
Month 3 uses this file to write the evaluation summary.

### `action_semantics.verification`

Functionality:
This file checks whether the expected month 1, month 2, and month 3 artifacts exist and contain valid nonempty JSONL rows.

Testing:
This should be run after every real pipeline run.

Relationship to other files:
The CLI calls it from `verify-repository` and `run-all`.

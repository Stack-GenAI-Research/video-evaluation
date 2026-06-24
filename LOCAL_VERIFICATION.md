# Local verification notes

The automated pipeline was checked locally with Python 3.13. The machine's default Python was 3.14, which is outside the project's declared Python range, so the virtual environment was created with Python 3.13.

```bash
/opt/homebrew/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python -m nltk.downloader verbnet wordnet omw-1.4 framenet_v17

.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests
.venv/bin/action-semantics --help
```

The test suite passed locally with 11 tests. Compilation and Ruff also passed, and the installed CLI displayed all commands, including `prepare-indexed-videos`, `run-indexed-video-analysis`, and `verify-structured-outputs`.

The following command ran the real private sample without creating fake retrieval inputs:

```bash
.venv/bin/action-semantics run-indexed-video-analysis \
  --indexed-videos-jsonl indexed-videos-250.jsonl \
  --output-dir /tmp/action-semantics-sample-results \
  --min-taxonomy-support 2

.venv/bin/action-semantics verify-structured-outputs \
  --output-dir /tmp/action-semantics-sample-results
```

The run flattened 250 videos into 1,703 clip records. Month 1 generated 8,823 action triples from 1,006 unique action lemmas and 1,006 VerbNet lookup rows; 63.1% of triples had an extracted object and 3.5% had a dependency-linked tool. Month 2 generated 1,006 FrameNet lookup rows, 8,823 SRL-style rows, and 660 `DIY-ActionNet v1` action assignments in 80 clusters. All required Month 1 and Month 2 JSONL artifacts were nonempty and had their required fields.

Month 3 was intentionally not run. `indexed-videos-250.jsonl` has no step records, pairwise relevance labels, or dense embeddings, so a dense-versus-structured retrieval score would not be real. No synthetic project dataset was added; the only invented rows remain small unit-test fixtures.

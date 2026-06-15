# Local verification notes

These are the checks that were run locally after the cleanup and documentation update.

```bash
python -m compileall -q src tests
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m action_semantics.cli --help
python -m pip install -e . --no-deps
action-semantics --help
```

The unit tests passed locally with 8 tests. The command line interface also opened correctly both through `python -m action_semantics.cli` and through the installed `action-semantics` command.

The full month 1 through month 3 pipeline was not run on the real Stesso data because this package does not include the private 67K clip export, transcripts, dense embeddings, or 2,077 pairwise comparison rows.

No synthetic project dataset was added to make the repository look complete. The only small invented examples are inside unit tests, where they are used only to check code behavior.

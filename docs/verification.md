# Current verification record

Verified July 13, 2026 on macOS 26.5.2 with Python 3.13.14.

This page records what was actually checked on the current repository. It is a
technical verification record, not a claim that retrieval quality has been
proven by human evaluation.

## Automated code checks

The main verification command was:

```bash
./scripts/run_local_pipeline.sh test
```

It completed successfully with:

```text
59 tests passed
All Ruff checks passed
Python source and tests compiled
CLI help rendered successfully
Bash syntax check passed
```

The tests cover nested input parsing, canonical IDs, duplicate merging,
extraction behavior, all three search methods, score guardrails, one-query and
batch comparison, timestamp resolution, blind assignment, worksheet overwrite
protection, review scoring, benchmark controls, tie-aware metrics, and index
freshness.

## Real sample ingest checks

The build used `indexed-videos-250.jsonl`, not synthetic input. Its final counts
were:

```text
source videos:                    250
raw nested clip rows:           1,703
valid clip annotations:        1,700
invalid rows quarantined:           3
redundant valid rows merged:       37
duplicate timestamp groups:        36
canonical searchable segments: 1,663
```

The canonical clip IDs are unique and based on video/timestamp identity. The
three non-positive intervals appear in `input/rejected_clips.jsonl`. Repeated
annotations are merged while alternate metadata and source provenance are
retained.

`index_manifest.json` records the source SHA-256 hash, hashes of generated
artifacts, spaCy model, extraction/schema versions, scorer version, and
candidate field policies. The current index passes its source, code, model,
configuration, and output-artifact freshness checks.

The manifest's `git_commit` field is the commit that existed at build time. It
is not intended to pretend that generated data was rebuilt for documentation-
only commits; the more specific code and artifact hashes are the operative
freshness checks.

## Extraction checks

The current real build produced:

```text
action records:                            8,899
distinct action lemmas:                    1,022
clips with at least one action:     1,296 / 1,663 (77.9%)
records with an object:             5,699 / 8,899 (64.0%)
records with a directly attached tool: 661 / 8,899 (7.4%)
VerbNet coverage of distinct actions:             70.9%
FrameNet coverage of distinct actions:            69.3%
```

The 8,899 action records come from these source fields after duplicate parsing
of provenance variants was removed:

```text
title:       1,255
description: 6,862
summary:       782
```

Tool and supply inventory context is preserved separately from a tool that is
directly attached to an action by the sentence grammar. The file named
`srl_roles.jsonl` contains dependency-based semantic roles produced by the
local spaCy pipeline; it is not output from a learned AllenNLP SRL model.

The exploratory DIY taxonomy contains useful diagnostics, but it is not used to
rank clips because its clusters have not been manually validated.

## Real search smoke checks

The following commands were run against the canonical sample:

```bash
./scripts/run_local_pipeline.sh search "remove old faucet" --method lexical
./scripts/run_local_pipeline.sh search "remove old faucet" --method structured
./scripts/run_local_pipeline.sh search "remove old faucet" --method hybrid
./scripts/run_local_pipeline.sh search "paint wall" --method hybrid --max-per-video 1
./scripts/run_local_pipeline.sh search "paint wall with primer" --method hybrid
./scripts/run_local_pipeline.sh search "tighten screw with screwdriver" \
  --method hybrid --max-per-video 1
```

Observed behavior:

- `remove old faucet` returned `Remove Faucet Stem` and `Remove Faucet Handle`
  in the first two positions for all three methods.
- `paint wall` exercised the short-command parser fallback and returned
  `Prepare and Paint Closet Walls` first.
- `paint wall with primer` returned that clip with a supply-context match of
  1.0. This verifies that parsed supplies participate in structured scoring.
- `tighten screw with screwdriver` returned `Tighten the Set Screws` first with
  action, object, and tool signals all equal to 1.0.
- The noun phrase `faucet removal` did not create a false structured action.
  Hybrid search fell back to lexical output and included a warning.

These examples verify that real search runs and that important score paths are
reachable. They are not an accuracy sample and should not be reported as proof
that one method is generally better.

## Batch comparison and review checks

The automated tests use controlled temporary inputs to verify that
`compare-batch`:

- requires one unique step ID and an exact contiguous top-*k* ranking;
- accepts canonical IDs or video/start/end timestamp references;
- resolves timestamps with a 0.05-second default tolerance;
- rejects missing and ambiguous references before search begins;
- reuses one loaded lexical and structured index across the batch;
- preserves the supplied old result order;
- writes neutral overlap statistics and a deterministic blinded worksheet;
- does not expose original/challenger method names in that worksheet; and
- writes `.generated` files instead of overwriting human labels or notes.

The scoring tests verify label parsing, worksheet identity, rank integrity,
hidden A/B assignment, missing-label coverage, Precision@*k*, Success@*k*,
wins/ties/losses, and paired bootstrap intervals.

There is currently no real `batch-comparison/` result in the sample output
directory. This is expected: the repository has not yet received the
supervisor's original query rankings. The tests establish that the machinery is
ready; they do not stand in for the research experiment.

## Benchmark checks

The benchmark rebuilt one fixed pool of 582 candidates and evaluated all
methods on the same 462 eligible queries. Candidate clip names and parent-video
text were excluded. Ambiguous query names, exact normalized paired phrases, and
remaining unparseable action queries were excluded as queries while their clips
stayed in the distractor pool.

The benchmark requires a positive score before assigning a target rank and uses
expected credit over exact score ties. The structured target had positive
evidence on 340 of 462 queries (73.6%) and a positive tie on 211 (45.7%).

The stored whole-corpus results were:

```text
method                 Hit@1   Hit@3   Hit@10   MRR
lexical TF-IDF          .632    .855     .933   .749
structured action       .264    .363     .471   .335
50/50 hybrid            .506    .615     .680   .577
```

Hybrid minus lexical Hit@1 was -0.126 with a video-cluster bootstrap 95%
interval of approximately [-0.184, -0.069]. In the within-video task, lexical
and hybrid Hit@1 were both .727, with an interval for their difference of
approximately [-0.049, 0.054]. The full interpretation and limitations are in
[Experiments and results](experiments-and-results.md).

## Manual checks still open

`quality/manual_review_sample.csv` contains 60 real extraction examples. Its
`action_correct`, `object_correct`, and `tool_correct` cells are intentionally
blank. No extraction precision number is available until a person labels that
worksheet.

The blinded old-versus-new relevance worksheet is also not available until real
original rankings are supplied. These are the two remaining manual checks; the
automatic commands cannot truthfully fill them in.

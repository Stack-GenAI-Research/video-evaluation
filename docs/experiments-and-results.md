# Experiments, results, and next steps

This project has two different kinds of evaluation. Keeping them separate is
important:

1. The **automatic development benchmark** can run now because it builds a
   proxy task from fields already paired inside the JSONL.
2. The **real old-versus-new experiment** needs the existing system's original
   rankings and human relevance judgments.

The first experiment tells me whether the code is learning a useful signal and
where it fails. Only the second can answer the main practical question: “Are
the new top three clips better than the old top three?”

## What data is usable now

The supplied export is enough to build and exercise search. Its canonical data
audit is:

| Item | Count |
|---|---:|
| Parent videos | 250 |
| Raw nested clip annotations | 1,703 |
| Invalid intervals rejected | 3 |
| Valid annotations | 1,700 |
| Redundant rows merged | 37 rows in 36 timestamp groups |
| Canonical searchable segments | 1,663 |
| Segments with description or goal fields for the benchmark | 582 |
| Segments with parsed tool metadata | 1,241 |

This corrects an earlier source of confusion: a nested clip annotation is not
always a distinct playable segment. Multiple annotations can refer to the same
video and timestamps.

The build extracted:

| Extraction measurement | Current result |
|---|---:|
| Action records | 8,899 |
| Distinct action lemmas | 1,022 |
| Clips with at least one action | 1,296 of 1,663 (77.9%) |
| Action records with an object | 5,699 of 8,899 (64.0%) |
| Action records with a directly attached tool | 661 of 8,899 (7.4%) |
| Distinct actions covered by VerbNet | 70.9% |
| Distinct actions covered by FrameNet | 69.3% |

These are coverage measurements. They say how often the parser produced a
field, not how often that field is correct. The 60-row extraction review is
still unlabeled, so I do not yet claim action, object, or tool precision.

## The automatic development benchmark

### Question and target

The JSONL does not contain human relevance labels. To get a repeatable early
test, the benchmark uses fields that are already paired for one timestamped
clip:

```text
query        = clip name
known target = that same timestamped clip
candidate    = clip description + goal + tools + supplies
```

For example, if a clip name describes removing a handle, the method should rank
that clip's remaining annotation fields highly without seeing the name in the
candidate text.

### Controls against easy answer leakage

The candidate representation excludes the clip name and all parent-video text.
The benchmark also excludes a query when:

- its normalized name is shared by more than one target;
- its exact normalized phrase appears in the paired candidate fields; or
- the structured parser cannot find a usable query action.

Excluded query clips remain in the candidate pool as distractors. Every search
method therefore receives the same 582 candidates and the same 462 eligible
queries.

These controls remove the most direct shortcuts, but they do not make the task
fully independent. Clip names and descriptions were generated together and may
still share partial wording or paraphrases. I therefore call this a
**direct-title and exact-phrase controlled development benchmark**, not a
leakage-free or final held-out test.

### Metrics in plain language

- **Hit@1** is the fraction of queries whose known target is ranked first.
- **Hit@3** is the fraction whose target appears in the first three positions.
- **Hit@10** uses the first ten positions.
- **MRR** rewards a correct target more when it appears near the top. A target
  at rank 1 contributes `1`, rank 2 contributes `1/2`, and so on.

A target receives a rank only when it has a positive score. If several clips
have exactly the same positive score, the metric averages over their possible
tied positions. It does not let alphabetical clip IDs decide which method gets
credit.

Uncertainty is estimated with a paired bootstrap grouped by source video.
Grouping matters because clips from one video are related rather than fully
independent examples.

## Current automatic results

### Whole-corpus retrieval

All 582 candidates can compete for each query.

| Method | Hit@1 | Hit@3 | Hit@10 | MRR |
|---|---:|---:|---:|---:|
| Lexical TF-IDF | 63.2% | 85.5% | 93.3% | 0.749 |
| Structured action | 26.4% | 36.3% | 47.1% | 0.335 |
| 50/50 hybrid | 50.6% | 61.5% | 68.0% | 0.577 |

The hybrid Hit@1 result is 12.6 percentage points below lexical search. The
video-cluster bootstrap 95% confidence interval for hybrid minus lexical is
approximately -18.4 to -6.9 points. On this proxy task, the current 50/50
hybrid is reliably worse than TF-IDF.

Structured search has positive target evidence for 340 of 462 queries (73.6%).
For 211 queries (45.7%), the target has the same positive score as at least one
other clip. Missing evidence and coarse ties are therefore two visible problems
with the present representation.

### Within-video reranking

The second task lets only clips from the target's source video compete. This is
a smaller and more topically controlled problem.

| Method | Hit@1 | Hit@3 | MRR |
|---|---:|---:|---:|
| Lexical TF-IDF | 72.7% | 92.9% | 0.834 |
| Structured action | 50.4% | 68.5% | 0.597 |
| 50/50 hybrid | 72.7% | 92.5% | 0.833 |

Lexical and hybrid search have the same observed Hit@1, but that does not prove
they are equivalent. The 95% confidence interval for hybrid minus lexical is
approximately -4.9 to +5.4 points. This run detected no reliable difference and
still allows either modest harm or modest benefit.

### What the result means

The current evidence does **not** support replacing lexical search with the
structured method across the full corpus. The structured representation is
useful for interpreting results and for distinguishing some close actions, but
its coverage and tie rate are not yet strong enough.

Within-topic reranking remains worth studying. Once a lexical or dense method
has found clips about the right subject, action features may help order those
close candidates. The within-video result is a reason to test that idea, not
evidence that it already works better.

Individual searches such as `remove old faucet`, `paint wall with primer`, and
`tighten screw with screwdriver` return sensible real clips. These are
functional smoke checks. A few good examples cannot estimate general accuracy.

## The real old-versus-new experiment

The comparison code is ready, but no real supervisor ranking batch exists in
this repository yet. Therefore no completed old-versus-new Precision@3 result
should be reported.

### What I need from the supervisor

For each project query or step, I need:

1. A stable query or step ID.
2. The exact text that was sent to the existing retrieval system.
3. Its original top three clips in their original rank order.
4. For each clip, either the canonical clip ID or its source video ID plus exact
   start and end timestamps.

The [original ranking data contract](../data_contracts/README.md) contains the
machine-readable JSONL example and validation rules. A useful first study would
contain 50–100 queries spread across multiple categories. The rank order must be
preserved; replacing the old list with newly generated lexical results would no
longer test the existing system.

I also need permission for a reviewer to inspect the pooled timestamped clips
and record blinded relevance judgments. The reviewer does not need to know which
method produced set A or set B.

### Experiment procedure

1. Validate and map all original clip references before running any new search.
2. Generate the structured or hybrid top three for every query.
3. Pool and shuffle the old and new clips in a blinded worksheet.
4. Label overall, action, object, and tool relevance with `yes` or `no`.
5. Score original and challenger Precision@3, Success@3, wins/ties/losses, label
   coverage, and the paired confidence interval.
6. Inspect disagreements to understand which actions and categories improve or
   fail.

The exact commands and worksheet columns are documented in
[Running the pipeline](running-the-pipeline.md#comparing-rankings).

The comparison tool itself never declares a winner from ranking overlap or from
its own retrieval score. Two lists can be different without either being more
relevant. The winner is determined only after independent human judgments.

## Data that is genuinely missing

The current sample does not contain:

- project query or step IDs paired with retrieval requests;
- the existing system's historical top-three results;
- their original ranks or retrieval scores;
- human relevance judgments;
- captions, transcripts, video frames, or dense embedding vectors.

The first four items are required for the real comparison. Captions,
transcripts, frames, and embeddings are optional research inputs that could
improve later systems, but their absence does not prevent this pipeline from
running.

A larger export in the same IndexedVideo format is useful for scale and category
coverage. It is not the main blocker. The supplied 250-video sample is already
enough for functional search and the development benchmark.

## Next technical work

The recommended order is:

1. Obtain the real old top-three rankings and run the blinded study.
2. Complete the 60-row extraction review so parser precision is measured.
3. Analyze the 107 narrative queries for which the current parser finds no
   action.
4. Reduce structured score ties and improve object/tool alignment.
5. Tune parser or hybrid changes on development videos only.
6. Freeze the chosen configuration and evaluate it once on held-out videos.
7. Run the unchanged pipeline on the larger IndexedVideo export.

The 50/50 hybrid weight is only a current default. Trying several weights on the
same 462 queries is acceptable for exploratory development, but the best of
those numbers must not be presented as an unbiased final result. A final study
needs separate held-out videos and preferably human judgments.

## Current research conclusion

The project has moved beyond data inspection: it now has reproducible indexing,
working search, neutral ranking comparison, blinded review generation, and an
automatic experiment. The automatic evidence has also revealed a real negative
result: structured action matching by itself is presently weaker than TF-IDF,
and the default hybrid hurts whole-corpus retrieval.

The research direction is now narrower and clearer. The next question is not
“Can we make action semantics run?” It is “Can better action features improve a
strong topical candidate set when relevance is judged by people?”

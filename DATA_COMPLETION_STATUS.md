# Data completion status

This repository has the code needed to run the first three months of Project 1. It now also has access to `indexed-videos-250.jsonl`, a private sample of 250 indexed videos with 1,703 nested clip records. The sample is enough to run and inspect the Month 1 and Month 2 structured-language pipeline. It is not enough to measure retrieval accuracy because it does not include project steps, pairwise comparison labels, or dense embedding vectors.

The project PDF describes the real data needed for this work: indexed video clips, `geminiMetaData`, transcripts, dense embeddings, and pairwise comparison rows. Those records are not inside this package, so I have not created fake clips, fake labels, fake dense embeddings, or fake final results.

What is complete in this repository:

- The month 1 extraction code is present.
- The month 2 FrameNet, SRL-style extraction, and taxonomy code is present.
- The month 3 scoring and pairwise evaluation code is present.
- The data contracts and SQL export guide are included.
- The repository can be installed and tested locally.
- The new `prepare-indexed-videos` command flattens the nested sample into stable clip records and writes a data-availability profile.
- The new `run-indexed-video-analysis` command runs Month 1 and Month 2 on the real sample, verifies the generated artifacts, and records why Month 3 was not run.
- The real sample run completed locally. It produced 8,823 action triples, 1,006 distinct action lemmas, 8,823 SRL-style role rows, and a 660-action, 80-cluster first-pass taxonomy. These are extraction outputs, not retrieval-effectiveness results.
- The pipeline now measures extraction quality automatically. Actions were found in 1,100 of 1,703 clips (64.6%), VerbNet covered 71.1% of action lemmas, and FrameNet covered 69.4%.
- A deterministic 60-row manual-review worksheet is generated at `quality/manual_review_sample.csv`.
- Record-level tool metadata is preserved separately from directly parsed tools and can be used as a fallback in structured scoring.

What still has to happen before the research dataset can be called complete:

- Export the full `clips.jsonl` from the real `IndexedVideoClip` data, or adapt the nested export using the new preparation command when appropriate.
- Export `steps.jsonl` from the real project-step data.
- Export `pairwise.jsonl` from the real `ClipPairComparison` data.
- Confirm that the dense embeddings are present in the clip and step export files.
- Run `validate-inputs`, `run-all`, and `verify-repository` on those files.
- Review a stratified sample of the extraction output manually before making research claims from it. The first sample run shows high object coverage (63.1%) but low dependency-linked tool coverage (3.5%), so tool attachment is an important error-analysis target.
- Label the generated review worksheet, summarize the error types, and report human-reviewed action/object/tool precision.

The code is intentionally strict about missing data. The sample runner stops before Month 3 rather than inventing steps, labels, or embeddings. This avoids the main risk in this project: producing tables that look finished but are based on incomplete or synthetic information.

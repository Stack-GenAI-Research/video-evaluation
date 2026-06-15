# Data completion status

This repository has the code needed to run the first three months of Project 1, but it does not include the private research dataset.

The project PDF describes the real data needed for this work: indexed video clips, `geminiMetaData`, transcripts, dense embeddings, and pairwise comparison rows. Those records are not inside this package, so I have not created fake clips, fake labels, fake dense embeddings, or fake final results.

What is complete in this repository:

- The month 1 extraction code is present.
- The month 2 FrameNet, SRL-style extraction, and taxonomy code is present.
- The month 3 scoring and pairwise evaluation code is present.
- The data contracts and SQL export guide are included.
- The repository can be installed and tested locally.

What still has to happen before the research dataset can be called complete:

- Export `clips.jsonl` from the real `IndexedVideoClip` data.
- Export `steps.jsonl` from the real project-step data.
- Export `pairwise.jsonl` from the real `ClipPairComparison` data.
- Confirm that the dense embeddings are present in the clip and step export files.
- Run `validate-inputs`, `run-all`, and `verify-repository` on those files.
- Review the extraction output manually before making research claims from it.

The code is intentionally strict about missing data. This helps avoid the main risk in this project, which would be producing tables that look finished but are based on incomplete or synthetic information.

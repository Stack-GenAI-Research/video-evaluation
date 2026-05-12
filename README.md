# Purdue Stack Research Project (2026)
Video evaluation data from API calls and different prompt formats

## Setting up the GenAI Scripts

The scripts I wrote are just wrappers for creating more flexibility around the prompt, output file, model,
and duration.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the API key(s):

```bash
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
export RUNWAYML_API_SECRET="..."
export REPLICATE_API_TOKEN="..."
```

## Generate a clip

```bash
python generate_openai_sora.py --prompt "Realistic close-up instructional DIY video: wrap PTFE tape clockwise on shower-arm threads." --out outputs/sora.mp4
python generate_google_veo.py --prompt "Realistic close-up instructional DIY video: tighten a compression nut on a toilet fill valve." --out outputs/veo.mp4
python generate_runway.py --prompt "Realistic close-up instructional DIY video: drill a pilot hole perpendicular to a pine board." --out outputs/runway_urls.txt
python generate_replicate_video.py --model "kwaivgi/kling-v3-video" --prompt "Realistic close-up instructional DIY video: add air to a tire while watching the gauge." --out outputs/kling.mp4
```

## Build a prompt queue from metadata

```bash
python batch_generate_prompt_queue.py --steps sample_steps.csv --architecture structured --out prompt_queue.csv
```

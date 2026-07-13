#!/usr/bin/env bash
# Run the local checks and Project 1 pipelines without remembering each command.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
SAMPLE_JSONL="${SAMPLE_JSONL:-$ROOT_DIR/indexed-videos-250.jsonl}"
PROJECT_OUTPUT_DIR="${PROJECT_OUTPUT_DIR:-$ROOT_DIR/project1_outputs}"
SAMPLE_OUTPUT_DIR="${SAMPLE_OUTPUT_DIR:-$PROJECT_OUTPUT_DIR/indexed-video-sample}"
COMMAND="${1:-all}"

usage() {
  cat <<'EOF'
Usage: ./scripts/run_local_pipeline.sh [setup|test|sample|review|all|full]

  setup   Create a Python 3.11-3.13 virtual environment and install dependencies.
  test    Compile the project, run pytest, run Ruff, and show CLI help.
  sample  Run the real IndexedVideo sample through Months 1 and 2.
  review  Summarize the human labels added to manual_review_sample.csv.
  all     Run setup, test, and sample. This is the normal local command.
  full    Run Months 1-3 on complete exports supplied through environment variables.

Optional environment variables:
  SAMPLE_JSONL        Path to indexed-videos-250.jsonl for the sample command.
  SAMPLE_OUTPUT_DIR   Destination for sample artifacts.
  PROJECT_OUTPUT_DIR  Parent output directory; defaults to project1_outputs/.
  VENV_DIR            Virtual environment location; defaults to .venv/.

The full command also requires CLIPS_JSONL, STEPS_JSONL, and PAIRWISE_JSONL.
EOF
}

find_python() {
  local candidate
  for candidate in python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done
  echo "Python 3.11, 3.12, or 3.13 is required. Install one and try again." >&2
  return 1
}

setup() {
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    local python_bin
    python_bin="$(find_python)"
    echo "Creating virtual environment with $python_bin"
    "$python_bin" -m venv "$VENV_DIR"
  fi

  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install -e "$ROOT_DIR[dev]"
  "$VENV_DIR/bin/python" -m spacy download en_core_web_sm
  "$VENV_DIR/bin/python" -m nltk.downloader verbnet wordnet omw-1.4 framenet_v17
}

ensure_environment() {
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    setup
  fi
}

run_tests() {
  ensure_environment
  "$VENV_DIR/bin/python" -m compileall -q "$ROOT_DIR/src" "$ROOT_DIR/tests"
  "$VENV_DIR/bin/python" -m pytest -q
  "$VENV_DIR/bin/ruff" check "$ROOT_DIR/src" "$ROOT_DIR/tests"
  "$VENV_DIR/bin/action-semantics" --help
}

run_sample() {
  ensure_environment
  if [[ ! -f "$SAMPLE_JSONL" ]]; then
    echo "Sample file not found: $SAMPLE_JSONL" >&2
    echo "Set SAMPLE_JSONL to the private IndexedVideo JSONL path and try again." >&2
    return 1
  fi
  "$VENV_DIR/bin/action-semantics" run-indexed-video-analysis \
    --indexed-videos-jsonl "$SAMPLE_JSONL" \
    --output-dir "$SAMPLE_OUTPUT_DIR" \
    --min-taxonomy-support 2
  "$VENV_DIR/bin/action-semantics" verify-structured-outputs \
    --output-dir "$SAMPLE_OUTPUT_DIR"
  echo
  echo "Sample report: $SAMPLE_OUTPUT_DIR/sample_analysis_report.json"
  echo "Review worksheet: $SAMPLE_OUTPUT_DIR/quality/manual_review_sample.csv"
}

summarize_review() {
  ensure_environment
  local review_csv="$SAMPLE_OUTPUT_DIR/quality/manual_review_sample.csv"
  if [[ ! -f "$review_csv" ]]; then
    echo "Review worksheet not found: $review_csv" >&2
    echo "Run the sample command first." >&2
    return 1
  fi
  "$VENV_DIR/bin/action-semantics" summarize-review \
    --review-csv "$review_csv" \
    --output-json "$SAMPLE_OUTPUT_DIR/quality/manual_review_results.json"
}

run_full() {
  ensure_environment
  : "${CLIPS_JSONL:?Set CLIPS_JSONL to the complete clips.jsonl export.}"
  : "${STEPS_JSONL:?Set STEPS_JSONL to the complete steps.jsonl export.}"
  : "${PAIRWISE_JSONL:?Set PAIRWISE_JSONL to the complete pairwise.jsonl export.}"
  "$VENV_DIR/bin/action-semantics" validate-inputs \
    --clips-jsonl "$CLIPS_JSONL" \
    --steps-jsonl "$STEPS_JSONL" \
    --pairwise-jsonl "$PAIRWISE_JSONL" \
    --output-dir "$PROJECT_OUTPUT_DIR"
  "$VENV_DIR/bin/action-semantics" run-all \
    --clips-jsonl "$CLIPS_JSONL" \
    --steps-jsonl "$STEPS_JSONL" \
    --pairwise-jsonl "$PAIRWISE_JSONL" \
    --output-dir "$PROJECT_OUTPUT_DIR" \
    --clip-limit 0 \
    --min-taxonomy-support 2 \
    --hybrid-alpha 0.5
}

case "$COMMAND" in
  setup) setup ;;
  test) run_tests ;;
  sample) run_sample ;;
  review) summarize_review ;;
  all)
    setup
    run_tests
    run_sample
    ;;
  full) run_full ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

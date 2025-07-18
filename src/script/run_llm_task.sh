#!/usr/bin/env bash
# Minimal wrapper for executing a single task with extract_info_generic.py.
#
# Edit the variables below to point at the desired TASK, input DATA_DIR, and
# output OUTPUT_DIR.  Any additional flags can be added to EXTRA_ARGS.

set -euo pipefail

# --- user-editable section ---------------------------------------------------
TASK="country_identification"                    # ← change me
DATA_DIR="/ephemeral/home/xiong/data/Fund/Factiva_News/2025"
OUTPUT_DIR="/ephemeral/home/xiong/data/Fund/Factiva_News/results"
EXTRA_ARGS=""   # e.g. "--batch_size 512 --test"
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/../run_llm_article_level.py"

echo "Running task: ${TASK}"
python "${PY_SCRIPT}" --task "${TASK}" \
  --data_dir "${DATA_DIR}" --output_dir "${OUTPUT_DIR}" ${EXTRA_ARGS}

echo "Done." 
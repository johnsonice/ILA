#!/usr/bin/env bash
# Run `extract_info_generic.py` for every task in PROMPT_REGISTRY.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/../run_llm_article_level.py"

# Edit these two lines to change input/output locations
DATA_DIR="/ephemeral/home/xiong/data/Fund/Factiva_News/2025"
OUTPUT_DIR="/ephemeral/home/xiong/data/Fund/Factiva_News/results"

# Extra flags passed straight through to each Python call
EXTRA_ARGS="$*"

# Get task list (space-separated)
TASKS=$(python - <<'PY'
from prompts.schemas import PROMPT_REGISTRY
print(*PROMPT_REGISTRY.keys())
PY
)

for TASK in ${TASKS}; do
  echo "\n=== ${TASK} ==="
  python "${PY_SCRIPT}" --task "${TASK}" \
    --data_dir "${DATA_DIR}" --output_dir "${OUTPUT_DIR}" ${EXTRA_ARGS}
 done

echo "All tasks done." 
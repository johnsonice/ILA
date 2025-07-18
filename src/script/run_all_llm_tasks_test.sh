#!/usr/bin/env bash
# Run extract_info_generic.py for every task, but in quick `--test` mode
# (only the first JSON file and first 20 articles).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/../extract_info_generic.py"

DATA_DIR="/ephemeral/home/xiong/data/Fund/Factiva_News/2025"
OUTPUT_DIR="/ephemeral/home/xiong/data/Fund/Factiva_News/results_test"

# Collect tasks
TASKS=$(python - <<'PY'
from prompts.schemas import PROMPT_REGISTRY
print(*PROMPT_REGISTRY.keys())
PY
)

for TASK in ${TASKS}; do
  echo -e "\n=== TEST ${TASK} ==="
  python "${PY_SCRIPT}" --task "${TASK}" \
    --data_dir "${DATA_DIR}" \
    --output_dir "${OUTPUT_DIR}" \
    --test
 done

echo "All test tasks done." 
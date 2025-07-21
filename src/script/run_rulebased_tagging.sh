set -euo pipefail
### example scropt to run rulebased tagging
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/../run_rulebased_tagging.py"
# run rulebased tagging
python "${PY_SCRIPT}" \
--data_dir /ephemeral/home/xiong/data/Fund/Factiva_News/2025 \
--output_dir /ephemeral/home/xiong/data/Fund/Factiva_News/results \
--jobs 1 \
--sub_jobs 16 \
--task_id rulebased_tagging \
--run_tests

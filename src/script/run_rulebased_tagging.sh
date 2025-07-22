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
#--run_tests

## in fund machine
# python run_rulebased_tagging.py --data_dir //data2/CommercialData/Factiva_Repository/2025 --output_dir "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results" --jobs 1 --sub_jobs 8 --task_id rulebased_tagging
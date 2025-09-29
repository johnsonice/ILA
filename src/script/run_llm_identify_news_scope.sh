#!/usr/bin/env bash
# Minimal wrapper for executing a single task with extract_info_generic.py.
#
# Edit the variables below to point at the desired TASK, input DATA_DIR, and
# output OUTPUT_DIR.  Any additional flags can be added to EXTRA_ARGS.

# set -euo pipefail
# SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# # --- user-editable section ---------------------------------------------------
# TASK="news_scope_classification"                    # ← change me
# DATA_DIR="//data2/CommercialData/Factiva_Repository/2025"
# OUTPUT_DIR="Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results"
# BATCH_SIZE= 8
# MODEL_ARGS="${SCRIPT_DIR}/../llm_args/netmind_qwen3_8b.json"
# API_KEY=$(grep "^netmid_api=" "${SCRIPT_DIR}/../../.env" | cut -d'=' -f2)
# # ---------------------------------------------------------------------------

# PY_SCRIPT="${SCRIPT_DIR}/../run_llm_article_level.py"

# echo "Running task: ${TASK}"
# python "${PY_SCRIPT}" --task "${TASK}" \
#   --data_dir "${DATA_DIR}" --output_dir "${OUTPUT_DIR}" --batch_size "${BATCH_SIZE}" \
#   --model_args "${MODEL_ARGS}" --api_key "${API_KEY}" 

# echo "Done." 

#########################
## in windows

cd "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\ILA\src"
## test run 
python run_llm_article_level.py --api_key "<API_Key>" --run_tests --task_id news_scope_classification --data_dir "//data2/CommercialData/Factiva_Repository" --output_dir "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\data\results" --batch_size 16 --model_args "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\ILA\src\llm_args\netmind_qwen3_8b.json"
## full run 
python run_llm_article_level.py --api_key "<API_Key>" --task_id news_scope_classification --data_dir "//data2/CommercialData/Factiva_Repository" --output_dir "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\data\results" --batch_size 16 --model_args "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\ILA\src\llm_args\netmind_qwen3_8b.json"

#%%
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
import sys
import argparse
from joblib import Parallel, delayed
warnings.filterwarnings('ignore')
# Add parent directory to path for imports
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from TPU_tagging_functions import TPUDetector
from src.run_rulebased_tagging import (extract_metadata, process_directory)
#%%

def _parse_args():
    parser = argparse.ArgumentParser( description="Run rule-based tagging and metadata extraction on Factiva JSON files.")
    parser.add_argument("--data_dir",default="/ephemeral/home/xiong/data/Fund/Factiva_News/2025",
        help=("Directory containing JSON article files (default: %(default)s)."),)
    parser.add_argument("--output_dir",default="/ephemeral/home/xiong/data/Fund/Factiva_News/results",
        help=("Directory where processed metadata JSON/CSV will be written (default: %(default)s)."),)
    parser.add_argument("--jobs",type=int,default=1,
        help="Number of parallel file-level jobs (default: 1).",)
    parser.add_argument("--sub_jobs",type=int,default=16,
        help="Number of per-file parallel jobs (default: 16).",)
    parser.add_argument("--strip_text",action="store_true",
        help="If set, body and snippet text are removed from the exported metadata.",)
    parser.add_argument("--run_tests",action="store_true",
        help="Run quick unit tests before processing.",)
    parser.add_argument("--task_id",type=str,default="TPU_tagging",
        help="Task ID for the processing (default: %(default)s).",)
    parser.add_argument("--quiet",action="store_true",
        help="Suppress progress messages for concise output.",)
    return parser.parse_args()


def main():
    args = _parse_args()
    start_time = datetime.now()
    # Determine verbosity level
    verbose_level = 0 if args.quiet else 1
    data_dir = args.data_dir
    output_dir = Path(args.output_dir) / args.task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build transformation pipeline
    tpu_tagger = TPUDetector()
    transform_funcs = [tpu_tagger.tag]

    if args.run_tests:
        print("Running unit tests... not yet implemented")
    else:
        tpu_job = process_directory(
            data_dir,
            transform_funcs,
            strip_text=args.strip_text,
            aggregate_output_file=None,
            n_jobs=args.jobs,
            sub_n_jobs=args.sub_jobs,
            verbose=verbose_level,
            return_df=False,
            return_content=False,
            task_id=args.task_id,
            export_dir=output_dir,
        )

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Finished processing in {str(duration).split('.')[0]}")

# Entry point
if __name__ == "__main__":
    main()

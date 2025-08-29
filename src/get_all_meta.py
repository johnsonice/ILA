#!/usr/bin/env python3
"""
Extract metadata from raw Factiva JSON files without any tagging.
This script follows the run_rulebased_tagging.py logic but only extracts metadata
by removing body and snippet fields from raw articles.

Usage:
    python get_all_meta.py --data_dir //data2/CommercialData/Factiva_Repository --output_dir "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/metadata"
"""

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
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from libs.utils import read_json, filter_unprocessed_files


def extract_metadata_only(
    articles,
    original_filename="",
    verbose=1,
    n_jobs=-1,
    return_df=False,
):
    """
    Extract metadata from articles by removing body and snippet fields.
    
    Parameters:
        articles (list): List of article dictionaries.
        original_filename (str, optional): Source filename. Defaults to "".
        verbose (int, optional): Verbosity level for parallel processing. Defaults to 1.
        n_jobs (int, optional): Number of jobs to run in parallel. Defaults to -1 (all processors).
        return_df (bool, optional): Return DataFrame if True, list if False. Defaults to False.
    
    Returns:
        pd.DataFrame or list: DataFrame containing article metadata (without body/snippet) if return_df=True,
                             otherwise list of dictionaries.
    """
    def process_single_article(article):
        if not isinstance(article, dict):
            return None
        
        # Create copy and remove text fields
        article_copy = article.copy()
        
        # Remove body and snippet fields to create metadata-only record
        article_copy.pop('body', None)
        article_copy.pop('snippet', None)
        
        # Add source filename for tracking
        article_copy['ILA_original_filename'] = original_filename
        
        return article_copy
    
    # Process articles in parallel
    processed = Parallel(n_jobs=n_jobs, verbose=verbose)(
        delayed(process_single_article)(article) for article in articles
    )
    
    # Filter out None values
    processed = [meta for meta in processed if meta is not None]
    
    if return_df:
        res = pd.DataFrame(processed)
    else:
        res = processed
        
    if verbose:
        print(f"  Extracted metadata from {len(processed)} articles")
        
    return res


def process_directory(
    data_dir,
    output_dir,
    n_jobs=-1,
    sub_n_jobs=8,
    verbose=1,
    return_df=False,
    task_id="metadata_extraction",
    return_content=False,
):
    """Process all JSON files in directory and extract metadata using parallel processing"""
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    
    # Find all JSON files recursively
    json_files = list(data_dir.rglob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {data_dir}")
        return None
    
    # Filter out already processed files
    json_files = filter_unprocessed_files(json_files, output_dir, task_id, verbose=True)
    
    if not json_files:
        print("All files have already been processed")
        return None
    
    def process_single_file(file_path):
        """Process a single JSON file and return metadata"""
        if verbose:
            print(f"Processing {file_path.name}...")
        
        try:
            articles = read_json(file_path)
        except Exception as e:
            if verbose:
                print(f"  Error reading {file_path.name}: {e}")
            return None
        
        if not articles:
            if verbose:
                print(f"  No articles found in {file_path.name}")
            return None
        
        try:
            metadata_res = extract_metadata_only(
                articles,
                original_filename=file_path.name,
                n_jobs=sub_n_jobs,
                return_df=return_df,
                verbose=verbose,
            )
            
            if verbose:
                print(f"  Extracted metadata from {len(metadata_res)} articles in {file_path.name}")
            
            # Create export filename based on original filename and task ID
            export_filename = file_path.stem
            if task_id:
                export_filename += f"_{task_id}"
            export_filename += ".csv" if return_df else ".json"
            export_path = output_dir / export_filename
            
            try:
                # Export as CSV if DataFrame, JSON if dict list
                if return_df and isinstance(metadata_res, pd.DataFrame):
                    metadata_res.to_csv(export_path, index=False)
                else:
                    # If list of dicts, write as JSON
                    with open(export_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata_res, f, indent=2, ensure_ascii=False)
                        
                if verbose:
                    print(f"  Exported metadata to {export_path}")
                    
                if return_content:
                    return metadata_res
                else:
                    return f"Successfully exported to {export_path}"
                    
            except Exception as e:
                if verbose:
                    print(f"  Error exporting to {export_path}: {e}")
                return None
                
        except Exception as e:
            if verbose:
                print(f"  Error processing {file_path.name}: {e}")
            return None
    
    # Process files in parallel
    print(f"\nProcessing {len(json_files)} files with {n_jobs} parallel jobs...")
    all_metadata = Parallel(n_jobs=n_jobs, verbose=verbose)(
        delayed(process_single_file)(file_path) for file_path in json_files
    )
    
    # Count successful processing
    successful = [item for item in all_metadata if item is not None]
    print(f"\nSuccessfully processed {len(successful)} out of {len(json_files)} files")
    
    if return_content:
        if return_df:
            # Filter out None values and non-DataFrames, then check for empty DataFrames
            valid_dfs = [df for df in all_metadata if df is not None and isinstance(df, pd.DataFrame) and not df.empty]
            if valid_dfs:
                combined_df = pd.concat(valid_dfs, ignore_index=True)
                if verbose:
                    print(f"Total articles in combined dataset: {len(combined_df)}")
                    print(f"Columns: {list(combined_df.columns)}")
                return combined_df
            else:
                return None
        else:
            # Filter out None values for list return
            return [item for item in all_metadata if item is not None]
    else:
        return "Finished processing all files"


def unit_test_extract_metadata(data_dir="//data2/CommercialData/Factiva_Repository"):
    """Unit test for extract_metadata_only function"""
    data_path = Path(data_dir)
    
    # Find first JSON file for testing
    json_files = list(data_path.rglob("*.json"))
    if not json_files:
        print(f"No JSON files found in {data_dir} for testing")
        return None
    
    test_file = json_files[0]
    print(f"Testing with file: {test_file}")
    
    try:
        articles = read_json(test_file)
        if articles:
            # Test with first 100 articles
            test_articles = articles[:100] if len(articles) > 100 else articles
            metadata_list = extract_metadata_only(
                test_articles,
                original_filename=test_file.name,
                return_df=False,
                verbose=1,
            )
            
            print(f"Successfully extracted metadata from {len(metadata_list)} test articles")
            if metadata_list:
                print(f"Sample metadata keys: {list(metadata_list[0].keys())}")
                # Check that body and snippet are removed
                sample = metadata_list[0]
                if 'body' not in sample and 'snippet' not in sample:
                    print("✅ Test passed: body and snippet successfully removed")
                else:
                    print("❌ Test failed: body or snippet still present")
                return metadata_list
        else:
            print(f"No articles found in test file {test_file}")
            return None
    except Exception as e:
        print(f"Error in unit test: {e}")
        return None


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Extract metadata from raw Factiva JSON files by removing body and snippet fields."
    )
    parser.add_argument(
        "--data_dir",
        default="//data2/CommercialData/Factiva_Repository",
        help="Directory containing raw JSON article files (default: %(default)s).",
    )
    parser.add_argument(
        "--output_dir",
        default="Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/metadata",
        help="Directory where extracted metadata will be written (default: %(default)s).",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="Number of parallel file-level jobs (default: 4).",
    )
    parser.add_argument(
        "--sub_jobs",
        type=int,
        default=8,
        help="Number of per-file parallel jobs (default: 8).",
    )
    parser.add_argument(
        "--return_df",
        action="store_true",
        help="Export as CSV format instead of JSON.",
    )
    parser.add_argument(
        "--run_tests",
        action="store_true",
        help="Run quick unit tests before processing.",
    )
    parser.add_argument(
        "--task_id",
        type=str,
        default="metadata_extraction",
        help="Task ID for the processing (default: %(default)s).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages for concise output.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    start_time = datetime.now()
    
    # Determine verbosity level
    verbose_level = 0 if args.quiet else 1
    
    # Setup directories
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Metadata Extraction Pipeline")
    print(f"==========================")
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Parallel jobs: {args.jobs} (file-level), {args.sub_jobs} (per-file)")
    print(f"Output format: {'CSV' if args.return_df else 'JSON'}")
    print(f"Task ID: {args.task_id}")
    
    # Check if data directory exists
    if not data_dir.exists():
        print(f"❌ Error: Data directory does not exist: {data_dir}")
        return
    
    if args.run_tests:
        print("\nRunning unit tests...")
        test_result = unit_test_extract_metadata(args.data_dir)
        if test_result is None:
            print("❌ Unit test failed")
            return
        else:
            print("✅ Unit test passed")
    
    print(f"\nStarting metadata extraction...")
    
    # Process all files
    result = process_directory(
        data_dir=data_dir,
        output_dir=output_dir,
        n_jobs=args.jobs,
        sub_n_jobs=args.sub_jobs,
        verbose=verbose_level,
        return_df=args.return_df,
        task_id=args.task_id,
        return_content=False,
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n✅ Finished processing in {str(duration).split('.')[0]}")
    print(f"Results saved to: {output_dir}")


# Entry point
if __name__ == "__main__":
    main()
#%%
## TPU Merge raw data
import sys,os
from pathlib import Path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
import argparse
import logging
from pathlib import Path
from tqdm import tqdm
from src.merge_tagged_results import Tag_Result_Merger
import pandas as pd
from datetime import datetime
    
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_and_aggregate_json_files(output_dir: str, 
                                  file_pattern: str = "*.json",
                                  keep_fields: list | None = None,
                                  verbose: bool = True) -> pd.DataFrame:
    """
    Load JSON files from output directory, aggregate all records, and convert to DataFrame.
    
    Steps:
    1) Get raw data files from output_dir, append all the records in the json files
    2) Turn dict objects into a pandas DataFrame 
    3) Do data cleanup including formatting publication_date into proper date format
    
    Args:
        output_dir (str): Directory containing the merged JSON files
        file_pattern (str): Pattern to match files (default: "*.json")
        verbose (bool): Whether to print progress information
        
    Returns:
        pd.DataFrame: Aggregated and cleaned DataFrame
    """
    # Step 1: Load all JSON files and aggregate records (only keep requested fields)
    all_records = _load_json_files(output_dir, file_pattern, keep_fields=keep_fields, verbose=verbose)
    
    if not all_records:
        logger.warning("No records found in any files")
        return pd.DataFrame()
    
    # Step 2: Convert to pandas DataFrame
    df = pd.DataFrame(all_records)
    if verbose:
        logger.info(f"Created DataFrame with shape: {df.shape}")
    
    # Step 3: Clean and format the data
    df = _clean_dataframe(df, verbose)
    
    return df


def _load_json_files(output_dir: str, 
                     file_pattern: str = "*.json", 
                     keep_fields: list | None = None,
                     verbose: bool = True) -> list:
    """Load and aggregate all JSON files matching the pattern.

    When `keep_fields` is provided, only those keys are extracted from each record to
    minimise memory usage while aggregating large numbers of JSON files.
    """
    output_path = Path(output_dir)
    
    if not output_path.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
    
    json_files = list(output_path.glob(file_pattern))
    if not json_files:
        logger.warning(f"No files found matching pattern '{file_pattern}' in {output_dir}")
        return []
    
    if verbose:
        logger.info(f"Found {len(json_files)} JSON files to process")
    all_records = []
    for file_path in tqdm(json_files, desc="Loading JSON files"):
        if verbose:
            logger.info(f"Processing file: {file_path.name}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Convert to list if single record
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                logger.warning(f"Unexpected data format in {file_path.name}")
                continue

            # If keep_fields is provided, only extract those keys per record to save memory
            if keep_fields:
                for record in data:
                    if isinstance(record, dict):
                        filtered = {k: record.get(k, None) for k in keep_fields}
                        all_records.append(filtered)
            else:
                for record in data:
                    if isinstance(record, dict):
                        all_records.append(record)

        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
            continue
    if verbose:
        logger.info(f"Loaded {len(all_records)} total records")
    
    return all_records


def _clean_dataframe(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Clean and format the DataFrame."""
    if df.empty:
        return df
    
    original_shape = df.shape
    
    # Convert any column containing 'publication_date' to datetime
    pub_date_cols = [col for col in df.columns if 'publication_date' in col.lower()]
    for col in pub_date_cols:
        df[col] = _convert_to_datetime(df[col])
        if verbose:
            logger.info(f"Converted {col} to datetime format")
    
    # Remove duplicates based on 'id' or 'an' field
    id_col = 'id' if 'id' in df.columns else 'an' if 'an' in df.columns else None
    if id_col:
        original_rows = len(df)
        df = df.drop_duplicates(subset=id_col, keep='last')
        if verbose and len(df) < original_rows:
            logger.info(f"Removed {original_rows - len(df)} duplicate records")
    
    if verbose:
        logger.info(f"Data cleanup completed: {original_shape} → {df.shape}")
    
    return df


def _convert_to_datetime(series: pd.Series) -> pd.Series:
    """Convert a series to datetime, handling various formats."""
    if series.empty:
        return series
    
    try:
        # Try numeric conversion first (timestamps)
        if series.dtype in ['int64', 'float64']:
            return pd.to_datetime(series, unit='ms', errors='coerce')
        
        # For string data, check if it looks like timestamps
        sample_val = str(series.dropna().iloc[0]) if not series.dropna().empty else ""
        if sample_val.isdigit():
            numeric_series = pd.to_numeric(series, errors='coerce')
            # Handle milliseconds vs seconds
            if numeric_series.max() > 1e10:
                return pd.to_datetime(numeric_series, unit='ms', errors='coerce')
            else:
                return pd.to_datetime(numeric_series, unit='s', errors='coerce')
        
        # Try standard datetime parsing
        return pd.to_datetime(series, errors='coerce')
        
    except Exception:
        return pd.to_datetime(series, errors='coerce')

def parse_arguments(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='TPU Merge raw data')
    
    parser.add_argument('--skip-merge', action='store_true',
                        help='Skip the merge step and only aggregate existing files')
    
    parser.add_argument('--input-dirs', nargs='+',
                        default=[
                            "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/metadata",
                            "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging",
                            "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/tpu_tagging", 
                        ],
                        help='Input directories containing files to merge')
    
    parser.add_argument('--output-dir',
                        default="Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/merged/TPU_new",
                        help='Output directory for merged files')
    
    return parser.parse_args(args)
#%%
if __name__ == "__main__":

    args = parse_arguments()
    # Setup directories
    dirs = args.input_dirs
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
#%%
    if not args.skip_merge:
        # Initialize merger
        merger = Tag_Result_Merger(tag_results_dirs=dirs, 
                                output_dir=output_dir)
        # Step 1: Find file groups
        file_groups = merger.discover_merge_files()
        print(f"Found {len(file_groups)} file groups")
        # Step 2: Merge files using 'id' field (this will save individual files)
        merged_results = merger.merge_files(file_groups, id_field="id",
                                            n_jobs=8,
                                            append_merge_results=False)
        print(f"Merged results saved to individual files in: {output_dir}")
   
    # Step 3: Load and aggregate all merged files into a single DataFrame
    print("\n" + "="*50)
    print("Loading and aggregating all merged files...")
    print("="*50)
    #%%
    # Use the new function to load, aggregate, and clean the data
    # Only keep the fields used by `src/TPU/TPU.ipynb` to save memory
    df = load_and_aggregate_json_files(
        output_dir=output_dir,
        file_pattern="*.json",
        keep_fields=[
            'id',  # article identifier
            'an',  # alternate id (some files use 'an')
            'ILA_publication_date',
            'publication_date',
            'ILA_TPU_Flag',
            'ILA_RulebasedCountryTag'
        ],
        verbose=True
    )

    df.to_pickle( Path(output_dir) / '../TPU_aggregated_data.pkl')
    df.to_csv( Path(output_dir) / '../TPU_aggregated_data.csv')
    print(f"Aggregated data saved to: {Path(output_dir) / '../TPU_aggregated_data.pkl'} and .csv")


# %%

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
# Add parent directory to path for imports|
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from libs.utils import read_json
from libs.meta_utils import construct_country_group_rex, tag_country
from libs.country_dict_full import get_dict
from functools import partial
from rule_based_tagging_functions import (
    create_country_tagging,
    extract_text_length,
    transform_dates,
    TradeTopicTagger,
)
#%%

def extract_metadata(
    articles,
    original_filename="",
    strip_text=False,
    transform_funcs=[],
    verbose=1,
    n_jobs=-1,
    return_df=False,
):
    """
    Extract metadata from articles into a DataFrame with parallel processing support.
    
    Parameters:
        articles (list): List of article dictionaries.
        original_filename (str, optional): Source filename. Defaults to "".
        transform_funcs (list[callable], optional): List of transformation functions to apply. Defaults to [].
        verbose (int, optional): Verbosity level for parallel processing. Defaults to 0.
        n_jobs (int, optional): Number of jobs to run in parallel. Defaults to -1 (all processors).
    
    Returns:
        pd.DataFrame or list: DataFrame containing article metadata (text content removed) if return_df=True,
                             otherwise list of dictionaries.
    """
    def process_single_article(article):
        if not isinstance(article, dict):
            return None
        # Create copy and remove text fields
        article_copy = article.copy()
        # process all transformations when provided 
        if transform_funcs:
            for transform_func in transform_funcs:
                article_copy = transform_func(article_copy)

        article_copy['ILA_original_filename'] = original_filename
        if strip_text:
            article_copy.pop('body', None)
            article_copy.pop('snippet', None)
        else:
            # Get all ILA_ keys and add id field
            ila_dict = {k: v for k, v in article_copy.items() if k.startswith('ILA_')}
            ila_dict['id'] = article_copy.get('an', None)  # Use 'an' field as id
            return ila_dict
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
        print(f"Processed {len(articles)} articles")
        
    return res

def process_directory(
    data_dir,
    transform_funcs,
    strip_text=False,
    aggregate_output_file=None,
    n_jobs=-1,
    sub_n_jobs=8,
    verbose=1,
    return_df=False,
    task_id=None,
    return_content=False,
    export_dir=None,
):
    """Process all JSON files in directory and extract metadata using parallel processing"""
    data_dir = Path(data_dir)
    json_files = list(data_dir.rglob("*.json"))
    
    def process_single_file(file_path,export_dir=export_dir,
                            task_id=task_id,return_df=return_df,
                            return_content=return_content):
        """Process a single JSON file and return metadata DataFrame"""
        if verbose:
            print(f"Processing {file_path.name}...")
        
        try:
            articles = read_json(file_path)
        except Exception as e:
            if verbose:
                print(f"  Error reading {file_path.name}: {e}")
            return None
        
        if articles:
            try:
                metadata_res = extract_metadata(
                    articles,
                    return_df=return_df,
                    original_filename=file_path.name,
                    transform_funcs=transform_funcs,
                    n_jobs=sub_n_jobs,
                    strip_text=strip_text,
                    verbose=verbose,
                )
                if verbose:
                    print(f"  Extracted {len(metadata_res)} articles from {file_path.name}")
                
                if export_dir:
                    # Create export filename based on original filename and task ID
                    export_filename = file_path.stem
                    if task_id:
                        export_filename += f"_{task_id}"
                    export_filename += "_metadata.csv" if isinstance(metadata_res, pd.DataFrame) else "_metadata.json"
                    export_path = Path(export_dir) / export_filename
                    
                    try:
                        # Export as CSV if DataFrame, JSON if dict list
                        if isinstance(metadata_res, pd.DataFrame):
                            metadata_res.to_csv(export_path, index=False)
                        else:
                            # If list of dicts, write directly
                            with open(export_path, 'w') as f:
                                json.dump(metadata_res, f, indent=4)  
                        if verbose:
                            print(f"Exported metadata to {export_path}")
                    except Exception as e:
                        if verbose:
                            print(f"  Error exporting to {export_path}: {e}")
                        return None
                    
                    if return_content:
                        return metadata_res
                    else:
                        return f"successfully exported to {export_path}"
                else:
                    if return_content:
                        return metadata_res
                    else:
                        return "processed successfully (no export directory specified)"
            except Exception as e:
                if verbose:
                    print(f"  Error processing {file_path.name}: {e}")
                return None
        else:
            if verbose:
                print(f"  No articles found in {file_path.name}")
            return None
    
    # Process files in parallel
    all_metadata = Parallel(n_jobs=n_jobs, verbose=verbose)(
        delayed(process_single_file)(file_path, export_dir=export_dir)
        for file_path in json_files
    )
    
    if not return_content:
        return "finished processing all files"
    else:
        if return_df:
            # Filter out None values and non-DataFrames, then check for empty DataFrames
            all_metadata = [df for df in all_metadata if df is not None and isinstance(df, pd.DataFrame) and not df.empty]
            if all_metadata:
                combined_df = pd.concat(all_metadata, ignore_index=True)
                if verbose:
                    print(f"\nTotal articles: {len(combined_df)}")
                    print(f"Columns: {list(combined_df.columns)}")
                
                if aggregate_output_file:
                    combined_df.to_csv(aggregate_output_file, index=False)
                    print(f"Saved metadata to {aggregate_output_file}")
                return combined_df
            else:
                return None
        else:
            # Filter out None values for list return
            all_metadata = [item for item in all_metadata if item is not None]
            return all_metadata


def unit_test_transformations():
    """Unit test for transformation functions list"""
    country_dict = get_dict()
    country_rex_dict = construct_country_group_rex(country_dict)

    # Create partial country tagging function with pre-bound regex dictionary
    country_tagger = partial(create_country_tagging, country_rex_dict=country_rex_dict)
    transform_funcs = [transform_dates, extract_text_length, country_tagger]

    # Sample article
    article = {
        "title": "US Economy Grows",
        "body": "The US economy is growing rapidly.",
        "publication_date": "1735689600",  # 2025-01-01 in seconds
    }

    for func in transform_funcs:
        article = func(article)

    assert 'ILA_WordCount' in article and article['ILA_WordCount'] > 0
    assert 'ILA_RulebasedCountryTag' in article and 'united states of america' in article['ILA_RulebasedCountryTag']

    print("Transformation unit test passed!")

def unit_test_extract_metadata(data_dir="/ephemeral/home/xiong/data/Fund/Factiva_News/2025"):
    """Unit test for extract_metadata with transformation list"""
    country_dict = get_dict()
    country_rex_dict = construct_country_group_rex(country_dict)

    country_tagger = partial(create_country_tagging, country_rex_dict=country_rex_dict)
    trade_topic_tagger = TradeTopicTagger()
    transform_funcs = [transform_dates, extract_text_length, country_tagger, trade_topic_tagger.tag]

    test_file = Path(data_dir) / "2025_articles_1.json"
    articles = read_json(test_file)
    if articles:
        metadata_df = extract_metadata(
            articles[:10000],
            original_filename=str(test_file),
            transform_funcs=transform_funcs,
            return_df=True,
            verbose=1,
        )
        print(f"\nExtracted metadata from {len(metadata_df)} articles in {test_file}")
        #print(metadata_df.head())
    else:
        print(f"No articles found in {test_file}")

    return metadata_df

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
    parser.add_argument("--task_id",type=str,default="rulebased_tagging",
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

    country_dict = get_dict()
    country_rex_dict = construct_country_group_rex(country_dict)

    # Build transformation pipeline
    country_tagger = partial(create_country_tagging, country_rex_dict=country_rex_dict)
    trade_topic_tagger = TradeTopicTagger()
    transform_funcs = [transform_dates, extract_text_length, country_tagger, trade_topic_tagger.tag]

    if args.run_tests:
        print("Running unit tests...")
        unit_test_transformations()
        unit_test_extract_metadata(data_dir)
    else:
        metadata_df = process_directory(
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

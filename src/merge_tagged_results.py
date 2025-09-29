### merge tagged results 
#%%

#!/usr/bin/env python3
"""
LLM Results Merger - Standalone Utility Script

This script merges tagged results using either rulebased or llm-extracted information together
using article IDs. It provides a complete set of modular functions for data processing.

"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter
import random
from tqdm import tqdm
from joblib import Parallel, delayed
from tenacity import retry, stop_after_attempt, wait_fixed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Tag_Result_Merger:
    """Main class for merging tagged results with raw data.
    This class can handle any number of tag results directories and will create
    file groups where each group contains corresponding files from all directories.
    """
    def __init__(self, 
                 tag_results_dirs = ["Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging",
                                     "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/tpu_tagging"],
                 output_dir = "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/merged/TPU"):
        """Initialize the Tag Result Merger.
        Args:
            tag_results_dirs (List[str]): List of directories containing tagged results.
                                        Can be any number of directories (2, 3, 4, etc.)
            output_dir (str): Directory where merged results will be saved.
        """
        if not tag_results_dirs:
            raise ValueError("At least one tag results directory must be provided")
        
        self.tagged_results_dirs = [Path(d) for d in tag_results_dirs]
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized Tag_Result_Merger with {len(self.tagged_results_dirs)} directories")
    
    def discover_merge_files(self):
        """Discover file groups based on their common name patterns.
        This function works with any number of tag results directories. It will find files
        that share the same base pattern (e.g., '2005_articles_1_') across all directories
        and group them together.
        Returns:
            List[Tuple[Path, ...]]: List of file groups. Each group is a tuple containing
                                  one file from each directory, in the same order as 
                                  self.tagged_results_dirs.
        Example:
            For 3 directories, each group will be a tuple of 3 files:
            (rulebased_file, tpu_file, llm_file)
        """
        file_groups = []
        num_dirs = len(self.tagged_results_dirs)
        
        logger.info(f"Discovering file groups across {num_dirs} directories")
        
        # Check if all tag_results_dirs exist
        for i, tag_dir in enumerate(self.tagged_results_dirs):
            if not tag_dir.exists():
                raise FileNotFoundError(f"Tag results directory {i+1} does not exist: {tag_dir}")
            else:
                logger.info(f"✅ Tag results directory {i+1} exists: {tag_dir}")
        
        # First, collect all files from all directories and extract their base patterns
        all_files_by_pattern = {}
        
        for dir_idx, tag_dir in enumerate(self.tagged_results_dirs):
            logger.info(f"Scanning directory {dir_idx + 1}/{num_dirs}: {tag_dir}")
            file_count = 0
            for file_path in tag_dir.glob("*.json"):
                filename = file_path.name
                file_count += 1
                # Extract the base pattern from filename
                parts = filename.split('_')
                base_pattern = None
                
                if len(parts) >= 2 and parts[0].isdigit() and parts[1] == 'articles':
                    if len(parts) >= 3 and parts[2].isdigit():
                        # Pattern: "2005_articles_1_" (has a number after articles)
                        base_pattern = f"{parts[0]}_articles_{parts[2]}_"
                    elif len(parts) >= 3 and not parts[2].isdigit():
                        # Pattern: "2005_articles_" (no number after articles)
                        base_pattern = f"{parts[0]}_articles_"
                
                if base_pattern:
                    if base_pattern not in all_files_by_pattern:
                        all_files_by_pattern[base_pattern] = [None] * num_dirs
                    
                    all_files_by_pattern[base_pattern][dir_idx] = file_path
            
            logger.info(f"  Found {file_count} JSON files in directory {dir_idx + 1}")
        
        logger.info(f"Found {len(all_files_by_pattern)} unique base patterns")
        
        # Now create file groups only for patterns that have files in all directories
        complete_groups = 0
        incomplete_groups = 0
        
        for base_pattern, file_list in all_files_by_pattern.items():
            if all(f is not None for f in file_list):
                file_groups.append(tuple(file_list))
                complete_groups += 1
                logger.debug(f"Added file group for pattern '{base_pattern}': {[f.name for f in file_list]}")
            else:
                incomplete_groups += 1
                missing_dirs = [i+1 for i, f in enumerate(file_list) if f is None]
                logger.debug(f"Pattern '{base_pattern}' missing files in directories: {missing_dirs}")
        
        logger.info(f"✅ Created {complete_groups} complete file groups")
        if incomplete_groups > 0:
            logger.info(f"⚠️  Skipped {incomplete_groups} incomplete patterns (missing files in some directories)")
        
        logger.info(f"Each file group contains {num_dirs} files (one from each directory)")
        return file_groups
    
    def merge_files(self, 
                    file_groups: List[Tuple[Path, ...]], 
                    id_field: str = "id",
                    save_disaggregrated_files: bool = True,
                    append_merge_results: bool = False,
                    n_jobs: int = -1,
                    verbose: int = 5) -> List[Dict]:
        """Merge JSON files from file groups using the specified ID field, with parallel processing.
        
        Args:
            file_groups: List of file groups from discover_merge_files()
            id_field: Field name to use for matching records (default: "id")
            save_disaggregrated_files: If True, save each group's merged records to a file.
            n_jobs: Number of parallel workers (joblib). Default -1 uses all cores.
            verbose: Joblib verbosity level (0=silent). Default 5 shows progress per batch.
        
        Returns:
            - If save_disaggregrated_files is False: List of merged group dicts.
            - If save_disaggregrated_files is True: List of saved file paths as strings.
        """
        total = len(file_groups)
        logger.info(f"Merging {total} file groups using '{id_field}' field with n_jobs={n_jobs}")

        def process_group(idx: int, file_group: Tuple[Path, ...]):
            merged = self._merge_single_group(file_group, id_field, idx)
            if not merged:
                return None
            if save_disaggregrated_files:
                # Derive output filename from first record's original filename if available
                try:
                    first_record = merged['records'][0] if merged.get('records') else {}
                    original_filename = first_record.get('ILA_original_filename')
                    if not original_filename:
                        # fallback to first file's stem
                        original_filename = file_group[0].stem
                    output_filename = f"{original_filename}.json"
                    output_path = self.output_dir / output_filename
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(merged['records'], f, indent=2, ensure_ascii=False)
                    return str(output_path)
                except Exception as e:
                    logger.error(f"Error saving merged group {idx}: {e}")
                    return None
            else:
                if append_merge_results:
                    return merged
                else:   
                    return {'group_index': idx, 'records': "skip to save memory"}  # Placeholder to save memory

        # Run in parallel
        results = Parallel(n_jobs=n_jobs, verbose=verbose)(
            delayed(process_group)(i, fg) for i, fg in enumerate(file_groups)
        )

        # Filter None
        results = [r for r in results if r is not None]

        if save_disaggregrated_files:
            logger.info(f"✅ Saved {len(results)}/{total} merged groups to {self.output_dir}")
        
        if append_merge_results:
            total_records = sum(len(group['records']) for group in results)
            logger.info(f"✅ Merged {len(results)} groups, {total_records} total records")
            return results
        else:
            logger.info(f"✅ Processed {len(results)} groups, results contain file index only to save memory")
            return results
            
    
    def _merge_single_group(self, file_group: Tuple[Path, ...], id_field: str, group_index: int) -> Dict:
        """Merge a single group of files."""
        records_by_id = {} # initiate merged records
        
        for file_path in file_group:
            file_records = self._load_json_file(file_path)
            for record in file_records:     
                ## get record id , also including original file where id is an       
                record_id = record.get(id_field)
                if not record_id:
                    record_id = record.get('an')
                if not record_id:
                    raise ValueError(f"Record missing '{id_field}' and 'an' fields in file {file_path.name}")

                # Initialize record if new
                if record_id not in records_by_id:
                    records_by_id[record_id] = {id_field: record_id}
    
                # Add data with source prefix
                self._add_record_data(records_by_id[record_id], record, id_field)
        
        if not records_by_id:
            return None
            
        return {
            'group_index': group_index,
            'source_files': [f.name for f in file_group],
            'records': list(records_by_id.values())
        }

    def _add_record_data(self, target_record: Dict, source_record: Dict, id_field: str) -> None:
        """Add data from source_record to target_record, prefixing keys with source_name."""
        for key, value in source_record.items():
            if key != id_field:
                target_record[key] = value

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def _load_json_file(self, file_path: Path) -> List[Dict]:
        """Load and validate JSON file with retry logic using tenacity."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.warning(f"{file_path.name}: Not a list, skipping")
                return None
                
            return data
            
        except Exception as e:
            logger.warning(f"Error loading {file_path}: {e}")
            raise  # Let tenacity handle the retry
    
    def save_merged_results(self, merged_results: List[Dict], filename: str = None) -> Path:
        """
        Save merged results to JSON file.
        """
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"merged_results_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(merged_results)} groups to: {output_path}")
        return output_path


#%%

if __name__ == "__main__":
    
    # Setup directories
    dirs = [
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging",
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/tpu_tagging",
    ]

    # Initialize merger
    merger = Tag_Result_Merger(tag_results_dirs=dirs)
    
    # Step 1: Find file groups
    file_groups = merger.discover_merge_files()
    print(f"Found {len(file_groups)} file groups")
    
    # Step 2: Merge files using 'id' field
    merged_results = merger.merge_files(file_groups, id_field="id")
    
    # # Step 3: Save results
    # output_path = merger.save_merged_results(merged_results,'TPU.json')
    # print(f"Results saved to: {output_path}")
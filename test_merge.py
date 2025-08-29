#!/usr/bin/env python3
"""
Test script for the merge function
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from merge_tagged_results import Tag_Result_Merger

def test_merge_function():
    """Test the merge function with a small subset of files"""
    
    dirs = [
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging",
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/tpu_tagging",
    ]

    merger = Tag_Result_Merger(tag_results_dirs=dirs)
    
    # Step 1: Discover file groups
    print("Step 1: Discovering file groups...")
    file_groups = merger.discover_merge_files()
    print(f"Found {len(file_groups)} file groups")
    
    # Test with just the first few groups to avoid processing too much data
    test_groups = file_groups[:3]  # Just first 3 groups
    print(f"Testing with first {len(test_groups)} groups:")
    
    for i, group in enumerate(test_groups):
        print(f"  Group {i+1}: {[f.name for f in group]}")
    
    # Step 2: Merge the files
    print("\nStep 2: Merging files...")
    merged_results = merger.merge_files(test_groups, id_field="id")
    print(f"Successfully merged {len(merged_results)} groups")
    
    # Show some sample results
    if merged_results:
        first_group = merged_results[0]
        print(f"\nSample from first group:")
        print(f"  Source files: {first_group['group_info']['source_files']}")
        print(f"  Total records: {first_group['group_info']['total_records']}")
        
        if first_group['data']:
            sample_record = first_group['data'][0]
            print(f"  Sample record keys: {list(sample_record.keys())}")
            if 'id' in sample_record:
                print(f"  Sample ID: {sample_record['id']}")
    
    # Step 3: Save results
    print("\nStep 3: Saving results...")
    output_path = merger.save_merged_results(merged_results, "test_merge_results.json")
    print(f"Saved to: {output_path}")
    
    return merged_results

if __name__ == "__main__":
    test_merge_function()

#!/usr/bin/env python3
"""Test the simplified merge function"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))
from merge_tagged_results import Tag_Result_Merger

def test_simplified_merge():
    dirs = [
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging",
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/tpu_tagging",
    ]

    merger = Tag_Result_Merger(tag_results_dirs=dirs)
    
    # Test with first 2 groups only
    file_groups = merger.discover_merge_files()
    test_groups = file_groups[:2]
    
    print(f"Testing with {len(test_groups)} groups:")
    for i, group in enumerate(test_groups):
        print(f"  Group {i+1}: {[f.name for f in group]}")
    
    # Merge and check results
    merged = merger.merge_files(test_groups)
    
    if merged:
        print(f"\nSuccess! Merged {len(merged)} groups")
        first_group = merged[0]
        print(f"First group has {len(first_group['records'])} records")
        if first_group['records']:
            sample = first_group['records'][0]
            print(f"Sample record keys: {list(sample.keys())[:5]}...")
    
    # Save test results
    output = merger.save_merged_results(merged, "test_simplified.json")
    print(f"Saved to: {output}")

if __name__ == "__main__":
    test_simplified_merge()

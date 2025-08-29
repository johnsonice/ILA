#!/usr/bin/env python3
"""
Test script to demonstrate the Tag_Result_Merger working with multiple directories
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from merge_tagged_results import Tag_Result_Merger

def test_with_2_directories():
    """Test with 2 directories (current setup)"""
    print("=" * 60)
    print("Testing with 2 directories")
    print("=" * 60)
    
    merger = Tag_Result_Merger()
    file_groups = merger.discover_merge_files()
    
    print(f"Result: Found {len(file_groups)} file groups")
    if file_groups:
        print(f"Each group contains {len(file_groups[0])} files")
        print("\nFirst 3 groups:")
        for i, group in enumerate(file_groups[:3]):
            print(f"  Group {i+1}:")
            for j, file_path in enumerate(group):
                print(f"    Dir {j+1}: {file_path.name}")

def test_with_3_directories():
    """Test with 3 directories (hypothetical third directory)"""
    print("\n" + "=" * 60)
    print("Testing with 3 directories (simulated)")
    print("=" * 60)
    
    # Create a hypothetical third directory path
    dirs = [
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging",
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/tpu_tagging",
        "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/hypothetical_llm_tagging"  # This doesn't exist
    ]
    
    try:
        merger = Tag_Result_Merger(tag_results_dirs=dirs)
        file_groups = merger.discover_merge_files()
        print(f"Result: Found {len(file_groups)} file groups")
    except FileNotFoundError as e:
        print(f"Expected error (third directory doesn't exist): {e}")

def test_with_1_directory():
    """Test with 1 directory"""
    print("\n" + "=" * 60)
    print("Testing with 1 directory")
    print("=" * 60)
    
    dirs = ["Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results/rulebased_tagging"]
    
    merger = Tag_Result_Merger(tag_results_dirs=dirs)
    file_groups = merger.discover_merge_files()
    
    print(f"Result: Found {len(file_groups)} file groups")
    if file_groups:
        print(f"Each group contains {len(file_groups[0])} files")
        print("\nFirst 3 groups:")
        for i, group in enumerate(file_groups[:3]):
            print(f"  Group {i+1}:")
            for j, file_path in enumerate(group):
                print(f"    Dir {j+1}: {file_path.name}")

def test_with_empty_list():
    """Test with empty directory list"""
    print("\n" + "=" * 60)
    print("Testing with empty directory list")
    print("=" * 60)
    
    try:
        merger = Tag_Result_Merger(tag_results_dirs=[])
    except ValueError as e:
        print(f"Expected error: {e}")

if __name__ == "__main__":
    test_with_2_directories()
    test_with_3_directories()
    test_with_1_directory()
    test_with_empty_list()

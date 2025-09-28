# TPU (Trade Policy Uncertainty) Processing Module

This module provides a comprehensive pipeline for detecting and analyzing Trade Policy Uncertainty (TPU) in news articles from the Factiva dataset. The TPU detection is based on rule-based pattern matching that identifies co-occurrence of trade-related terms and uncertainty-related terms within a 10-word window.

## 📁 Module Structure

```
TPU/
├── TPU_tagging.py                    # Main execution script for TPU tagging
├── TPU_tagging_functions.py          # Core TPU detection logic and functions
├── TPU_merge_raw_data.py            # Data aggregation and merging utilities
├── run_TPU_tagging.sh               # Shell script for batch processing
└── unit_test/
    └── test_tpu_examples.py         # Comprehensive test suite with examples
```

## 🔍 Core Components

### 1. TPU_tagging_functions.py
**Purpose**: Contains the core `TPUDetector` class that implements the rule-based TPU detection algorithm.

**Key Features**:
- **Trade Terms Detection**: Identifies trade-related terms including:
  - Trade agreements (USMCA, NAFTA, WTO, FTA, etc.)
  - Trade policies and measures (tariffs, import/export restrictions, sanctions)
  - Trade disputes and negotiations
- **Uncertainty Terms Detection**: Identifies uncertainty-related terms including:
  - Direct uncertainty terms (uncertain, unpredictable, volatile)
  - Crisis and risk terms (crisis, threat, danger, concerns)
  - Economic instability terms (recession, downturn, fragility)
- **Co-occurrence Detection**: Uses regex patterns to detect when trade and uncertainty terms appear within 10 words of each other
- **Text Normalization**: Preserves acronyms (WTO, IMF, etc.) while cleaning text

**Main Methods**:
- `detect_tpu(text)`: Returns True if TPU pattern is detected
- `tag(article)`: Tags a full article dictionary with TPU flags and reference text
- `normalize_text_preserving_acronyms(text)`: Cleans text while preserving important acronyms

### 2. TPU_tagging.py
**Purpose**: Main execution script that processes entire directories of Factiva JSON files.

**Key Features**:
- Command-line interface with multiple configuration options
- Parallel processing support (both file-level and article-level parallelism)
- Integration with the broader ILA pipeline infrastructure
- Configurable output options (with/without full text)

**Usage Example**:
```bash
python TPU_tagging.py \
    --data_dir "/path/to/factiva/json/files" \
    --output_dir "/path/to/results" \
    --jobs 4 \
    --sub_jobs 16 \
    --task_id "TPU_tagging"
```

### 3. TPU_merge_raw_data.py
**Purpose**: Handles post-processing, merging, and aggregation of TPU-tagged results.

**Key Features**:
- **File Aggregation**: Loads and combines multiple JSON result files
- **Data Cleaning**: Standardizes date formats, removes duplicates, handles missing values
- **Multi-source Merging**: Combines results from metadata extraction, rule-based tagging, and TPU tagging
- **Export Options**: Saves results as both CSV and pickle formats for downstream analysis

**Main Functions**:
- `load_and_aggregate_json_files()`: Aggregates all JSON files into a single DataFrame
- `_clean_dataframe()`: Performs data cleaning and standardization
- `_convert_to_datetime()`: Handles various timestamp formats

### 4. unit_test/test_tpu_examples.py
**Purpose**: Comprehensive test suite that validates TPU detection accuracy across various scenarios.

**Test Categories**:
- **Positive Examples**: Sentences that should trigger TPU detection (35+ test cases)
- **Negative Examples**: Sentences that should NOT trigger TPU detection (20+ test cases)
- **Edge Cases**: Special scenarios including empty strings, punctuation, case sensitivity
- **Performance Metrics**: Calculates precision, recall, and accuracy

## 🚀 Quick Start Guide

### Step 1: Run TPU Tagging on Raw Data
```bash
cd Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\ILA\src\TPU
python TPU_tagging.py \
    --data_dir //data2/CommercialData/Factiva_Repository/2025 \
    --output_dir "Q:/DATA/SPRAI/Chengyu Huang/8_Data_Science/Factiva_News_Project/data/results" \
    --jobs 1 --sub_jobs 8 --task_id tpu_tagging
```

### Step 2: Merge and Aggregate Results
```bash
python TPU_merge_raw_data.py 
```
## 📊 Output Format

Each processed article receives the following TPU-related fields:

- **`ILA_TPU_Flag`** (boolean): True if TPU pattern detected, False otherwise
- **`ILA_TPU_Reference`** (string): Reference text (title + snippet + first 5 sentences) where TPU was detected (limited to 500 characters)




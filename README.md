# GenAI-Powered Intelligent Language Agents (ILA) for IMF Surveillance

A comprehensive, high-performance modular system for merging LLM-extracted country information back to original raw news articles using article IDs, with advanced search capabilities and quality checking.

## 🎯 Overview

This project provides both Jupyter notebook and standalone Python script interfaces for:
- **Merging**: LLM results with raw article data using ID-based matching
- **Advanced Search**: Multiple search modes (exact, partial, word-based) with multi-country support
- **High Performance**: Optimized algorithms with indexing for ultra-fast searches
- **Rule-based Tagging & Metadata Extraction**: Automatic date normalization, word/sentence statistics, country tagging, and trade-topic detection for large Factiva JSON dumps
- **TPU Detection**: Advanced Trade Policy Uncertainty detection using sophisticated pattern matching and proximity algorithms
- **Sampling**: Multiple methods (random, first, last, index-based) with reproducible seeding
- **Analysis**: Country distribution statistics and coverage analysis
- **Validation**: Quality checks and merge accuracy validation

## 📁 Project Structure

```
dev/ILA/
├── src/
│   ├── merge_llm_results.py              # CLI for merging & advanced search
│   ├── run_rulebased_tagging.py          # CLI for metadata extraction & tagging
│   ├── rule_based_tagging_functions.py   # Transformation utilities
│   ├── run_llm_article_level.py          # Batch LLM processing (article-level)
│   ├── TPU/                              # Trade Policy Uncertainty detection
│   │   ├── TPU_tagging.py                # CLI for TPU detection & tagging
│   │   ├── TPU_tagging_functions.py      # TPU detection algorithms
│   │   ├── run_TPU_tagging.sh            # Shell script for TPU tagging
│   │   └── unit_test/                    # Unit tests for TPU functionality
│   └── script/                           # Shell helpers
├── libs/                                 # Shared helper modules (utils, meta_utils, …)
├── notebook/
│   ├── post_process_llm_results.ipynb    # Interactive exploration of merge/search
│   └── (other notebooks)
└── README.md                             # This file
```

## 🚀 Quick Start

### Environment Setup
```bash
# Activate the factiva conda environment
conda activate factiva

# Or use the factiva python directly
/ephemeral/home/xiong/miniconda3/envs/factiva/bin/python
```

### Command Line Usage

#### Basic Operations
```bash
# Display help
python ~/dev/ILA/merge_llm_results.py --help

# Merge all file pairs
python ~/dev/ILA/merge_llm_results.py --merge-all

# Get country statistics
python ~/dev/ILA/merge_llm_results.py --get-stats
```

#### Advanced Search Operations
```bash
# Basic country search
python ~/dev/ILA/merge_llm_results.py --search-country "Spain" --limit 5

# Multiple countries search (OR operation)
python ~/dev/ILA/merge_llm_results.py --search-multiple-countries "Spain" "France" "Germany" --limit 5

# Advanced search with different matching modes
python ~/dev/ILA/merge_llm_results.py --search-country "United" --match-mode partial --limit 3
python ~/dev/ILA/merge_llm_results.py --search-country "United States" --match-mode any --limit 3

# Case-sensitive search
python ~/dev/ILA/merge_llm_results.py --search-country "china" --case-sensitive --limit 3
```

#### Performance & Indexing
```bash
# Create search index for ultra-fast searches
python ~/dev/ILA/merge_llm_results.py --create-index

# Benchmark search performance
python ~/dev/ILA/merge_llm_results.py --benchmark-search

# Find specific article by ID
python ~/dev/ILA/merge_llm_results.py --find-article "SURON00020250428el4s000fj"
```

#### Rule-Based Tagging & Metadata Extraction
```bash
# Display help
python ~/dev/ILA/src/run_rulebased_tagging.py --help

# Quick unit tests for transformation pipeline
python ~/dev/ILA/src/run_rulebased_tagging.py --run_tests

# Process an entire directory with parallelism (file-level 4 jobs, 16 per-file jobs)
python ~/dev/ILA/src/run_rulebased_tagging.py \
  --data_dir /ephemeral/home/xiong/data/Fund/Factiva_News/2025 \
  --output_dir /ephemeral/home/xiong/data/Fund/Factiva_News/results \
  --jobs 4 --sub_jobs 16 --task_id rulebased_tagging

# Strip full text from exported metadata (saves space)
python ~/dev/ILA/src/run_rulebased_tagging.py --strip_text
```

#### Trade Policy Uncertainty (TPU) Detection
```bash
# Run TPU detection on articles with parallelism
python ~/dev/ILA/src/TPU/TPU_tagging.py \
  --data_dir /path/to/data --output_dir /path/to/results \
  --jobs 1 --sub_jobs 8 --task_id tpu_tagging

# Use shell script for convenience (pre-configured paths)
bash ~/dev/ILA/src/TPU/run_TPU_tagging.sh
```

The same commands are wrapped by `src/script/run_rulebased_tagging.sh` for convenience (pre-configured paths & sensible defaults).

### Jupyter Notebook Usage

Open `notebook/post_process_llm_results.ipynb` and run the cells to:
1. **Setup**: Initialize paths and load dependencies
2. **Discovery**: Find raw data and LLM results file pairs
3. **Merging**: Process all file pairs and create enhanced articles
4. **Analysis**: Run quality checks and statistical analysis
5. **Advanced Search**: Test optimized search capabilities with different modes
6. **Performance**: Compare regular vs indexed search performance

## 🛠️ Key Features

### Optimized Search Functions

#### Core Search Capabilities
- `search_articles_by_country()`: **Multi-mode search** with exact, partial, and word matching
- `search_articles_by_multiple_criteria()`: **Advanced filtering** by countries, sources, date ranges
- `get_country_search_index()`: **Create search indexes** for ultra-fast lookups
- `search_articles_by_country_indexed()`: **Lightning-fast search** using pre-built indexes

#### Search Modes
- **Exact Match**: `match_mode='exact'` - Precise country name matching
- **Partial Match**: `match_mode='partial'` - Substring matching within country names
- **Word Match**: `match_mode='any'` - Any word from search term matches any word in country names

#### Performance Features
- **Indexed Search**: Up to **7000x faster** than regular search
- **Multi-Country Search**: Search for articles mentioning any of multiple countries
- **Case-Sensitive Options**: Flexible case handling for precise searches
- **Batch Processing**: Optimized for large datasets (88K+ articles)

### Other Core Utilities
- `load_enhanced_articles()`: Load JSON files with flexible file selection
- `sample_articles()`: Multiple sampling methods with reproducible seeding
- `find_article_by_id()`: Fast ID-based article lookup
- `get_country_statistics()`: Comprehensive country distribution analysis
- `validate_merge_accuracy()`: Quality validation with detailed reporting

### Display Functions
- `display_article()`: Pretty-print single article details
- `display_article_list()`: Formatted list display with optional detail view
- `display_validation_results()`: Formatted validation result display
- `display_country_statistics()`: Statistical analysis visualization

### Rule-Based Tagging Pipeline

These helper functions power the **run_rulebased_tagging.py** CLI and can be freely composed in your own data-processing pipeline:

- `transform_dates()` — Convert UNIX second/millisecond timestamps into ISO strings (YYYY-MM-DD HH:MM:SS)
- `extract_text_length()` — Compute `ILA_WordCount` and `ILA_SentenceCount` across title/body/snippet.
- `create_country_tagging()` — Fast country detection based on extensive regex dictionaries (`libs.country_dict_full`). Populates `ILA_RulebasedCountryTag`.
- `TradeTopicTagger().tag()` — Detects more than 120 trade-related keywords (tariffs, FTA, supply-chain, WTO, etc.) and sets `ILA_TradeTopicTag`, related keyword list, and counts.

All functions follow a **pure functional style**: they accept and return an article **dict** without mutating the original object, making them easy to unit-test and chain together.

### TPU (Trade Policy Uncertainty) Detection

Advanced pattern matching system for detecting trade policy uncertainty in news articles:

- `TPUDetector().tag()` — Detects co-occurrence of trade and uncertainty terms within 10-word proximity
- **Trade Terms**: USMCA, NAFTA, WTO, tariffs, trade wars, import/export restrictions (50+ terms)
- **Uncertainty Terms**: volatility, concerns, risks, threats, ambiguity (80+ terms)
- **Output**: `ILA_TPU_Flag` (boolean) and `ILA_TPU_Reference` (context snippet)

### Performance Optimization Workflow
```python
# Create index once
country_index = get_country_search_index(articles)

# Reuse index for multiple fast searches
spain_results = search_articles_by_country_indexed('spain', country_index, articles)
france_results = search_articles_by_country_indexed('france', country_index, articles)
germany_results = search_articles_by_country_indexed('germany', country_index, articles)

# Save index for future sessions
import json
with open('country_index.json', 'w') as f:
    json.dump(country_index, f)
```

### Advanced Search with Multiple Criteria
```python
# Search with multiple filters
results = search_articles_by_multiple_criteria(
    countries=['Spain', 'France'],
    source_names=['El País', 'Le Monde'],
    date_range=('2025-01-01', '2025-12-31'),
    enhanced_articles=articles
)
```

### TPU Detection Examples
```python
# Initialize and use TPU detector
from src.TPU.TPU_tagging_functions import TPUDetector
tpu_detector = TPUDetector()

# Tag article with TPU detection
article = {'title': 'Trade war uncertainty affects markets', 'body': '...'}
tagged_article = tpu_detector.tag(article)
print(f"TPU: {tagged_article['ILA_TPU_Flag']}")
```

## 🔧 Configuration

### Default Paths
- **Raw Data**: `/ephemeral/home/xiong/data/Fund/Factiva_News/2025/`
- **LLM Results**: `/ephemeral/home/xiong/data/Fund/Factiva_News/results/`
- **Rule-Based Metadata**: `/ephemeral/home/xiong/data/Fund/Factiva_News/results/rulebased_tagging/`
- **TPU Tagging Results**: `/ephemeral/home/xiong/data/Fund/Factiva_News/results/tpu_tagging/`
- **Enhanced Output**: `/ephemeral/home/xiong/data/Fund/Factiva_News/enhanced/`

### Customization
```bash
# Custom directories with advanced search
python merge_llm_results.py \
  --raw-data-dir /custom/raw/path \
  --llm-results-dir /custom/llm/path \
  --output-dir /custom/output/path \
  --search-multiple-countries "Spain" "France" \
  --match-mode partial --limit 10

# Custom TPU tagging with specific parameters
python src/TPU/TPU_tagging.py \
  --data_dir /custom/data/path \
  --output_dir /custom/output/path \
  --jobs 2 --sub_jobs 16 \
  --task_id custom_tpu_analysis \
  --strip_text
```

### Complete Processing Pipeline
```bash
# Step 1: Rule-based tagging and metadata extraction
python src/run_rulebased_tagging.py --data_dir /path/to/data --task_id rulebased_tagging

# Step 2: TPU detection and tagging
python src/TPU/TPU_tagging.py --data_dir /path/to/data --task_id tpu_tagging

# Step 3: LLM processing (if needed)
python src/run_llm_article_level.py --data_dir /path/to/data

# Step 4: Merge all results
python merge_llm_results.py --merge-all

# Step 5: Create search indexes for fast querying
python merge_llm_results.py --create-index
```


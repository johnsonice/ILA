#!/usr/bin/env python3
"""
LLM Results Merger - Standalone Utility Script

This script merges LLM-extracted country information back to original raw news articles
using article IDs. It provides a complete set of modular functions for data processing
and quality checking.

Usage:
    python merge_llm_results.py --help
    python merge_llm_results.py --merge-all
    python merge_llm_results.py --validate
    python merge_llm_results.py --search-country "Spain" --limit 5
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter
import random
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMResultsMerger:
    """Main class for merging LLM results with raw data."""
    
    def __init__(self, 
                 raw_data_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/2025/",
                 llm_results_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/results/",
                 output_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/enhanced/"):
        self.raw_data_dir = Path(raw_data_dir)
        self.llm_results_dir = Path(llm_results_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def discover_file_pairs(self) -> List[Tuple[Path, Path]]:
        """Discover pairs of raw data files and their corresponding LLM results."""
        file_pairs = []
        raw_files = list(self.raw_data_dir.glob("*articles*.json"))
        
        for raw_file in raw_files:
            base_name = raw_file.stem
            llm_results_file = self.llm_results_dir / f"{base_name}_countries_llm.json"
            
            if llm_results_file.exists():
                file_pairs.append((raw_file, llm_results_file))
                logger.info(f"✅ Found pair: {raw_file.name} ↔ {llm_results_file.name}")
            else:
                logger.warning(f"⚠️  No LLM results found for {raw_file.name}")
        
        return file_pairs
    
    def merge_llm_results_with_raw_data(self, raw_file: Path, llm_results_file: Path) -> Tuple[List[Dict], Dict]:
        """Merge LLM-extracted country information with raw article data."""
        # Load raw data
        logger.info(f"Loading raw data from {raw_file.name}")
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_articles = json.load(f)
        
        # Load LLM results
        logger.info(f"Loading LLM results from {llm_results_file.name}")
        with open(llm_results_file, 'r', encoding='utf-8') as f:
            llm_results = json.load(f)
        
        # Create mapping from ID to country information
        country_mapping = {result['id']: result for result in llm_results}
        
        # Merge data
        enhanced_articles = []
        merge_stats = {
            'total_raw_articles': len(raw_articles),
            'total_llm_results': len(llm_results),
            'successful_merges': 0,
            'missing_llm_results': 0,
            'duplicate_ids': 0
        }
        
        # Track IDs for duplicate detection
        seen_ids = set()
        
        for article in tqdm(raw_articles, desc="Merging articles"):
            article_id = article.get('an')
            
            if not article_id:
                logger.warning(f"Article missing 'an' field: {article.get('title', 'Unknown title')[:50]}")
                enhanced_articles.append(article)
                continue
            
            # Check for duplicate IDs
            if article_id in seen_ids:
                merge_stats['duplicate_ids'] += 1
                logger.warning(f"Duplicate article ID found: {article_id}")
            seen_ids.add(article_id)
            
            # Enhanced article with original data
            enhanced_article = article.copy()
            
            # Add country information if available
            if article_id in country_mapping:
                country_info = country_mapping[article_id]
                enhanced_article['llm_main_country'] = country_info.get('main_country')
                enhanced_article['llm_other_countries'] = country_info.get('other_countries', [])
                merge_stats['successful_merges'] += 1
            else:
                # No LLM results for this article
                enhanced_article['llm_main_country'] = None
                enhanced_article['llm_other_countries'] = []
                merge_stats['missing_llm_results'] += 1
            
            enhanced_articles.append(enhanced_article)
        
        # Calculate merge success rate
        merge_stats['merge_success_rate'] = (merge_stats['successful_merges'] / merge_stats['total_raw_articles']) * 100
        
        logger.info(f"Merge complete: {merge_stats['successful_merges']}/{merge_stats['total_raw_articles']} "
                    f"({merge_stats['merge_success_rate']:.1f}%) successful merges")
        
        return enhanced_articles, merge_stats
    
    def process_all_file_pairs(self) -> List[Dict]:
        """Process all discovered file pairs and return merge statistics."""
        file_pairs = self.discover_file_pairs()
        all_merge_stats = []
        
        logger.info(f"Processing {len(file_pairs)} file pairs")
        
        for i, (raw_file, llm_results_file) in enumerate(file_pairs, 1):
            logger.info(f"[{i}/{len(file_pairs)}] Processing: {raw_file.name}")
            
            try:
                # Merge LLM results with raw data
                enhanced_articles, merge_stats = self.merge_llm_results_with_raw_data(raw_file, llm_results_file)
                
                # Save enhanced articles
                output_file = self.output_dir / f"enhanced_{raw_file.name}"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_articles, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Saved enhanced articles to {output_file}")
                
                # Store stats
                merge_stats['file_pair'] = (raw_file.name, llm_results_file.name)
                all_merge_stats.append(merge_stats)
                
            except Exception as e:
                logger.error(f"❌ Error processing {raw_file.name}: {str(e)}")
                continue
        
        return all_merge_stats


class LLMResultsAnalyzer:
    """Analysis and search utilities for enhanced articles."""
    
    def __init__(self, output_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/enhanced/"):
        self.output_dir = Path(output_dir)
    
    def load_enhanced_articles(self, file_pattern: str = "enhanced_*.json") -> Optional[List[Dict]]:
        """Load enhanced articles from JSON files."""
        enhanced_files = list(self.output_dir.glob(file_pattern))
        
        if not enhanced_files:
            logger.warning("No enhanced files found")
            return None
        
        # Load from first file or combine multiple files
        if len(enhanced_files) == 1:
            with open(enhanced_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Combine multiple files
            all_articles = []
            for file_path in enhanced_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    articles = json.load(f)
                    all_articles.extend(articles)
            return all_articles
    
    def sample_articles(self, articles: List[Dict], sample_size: int = 10, 
                       method: str = 'random', seed: Optional[int] = None,
                       indices: Optional[List[int]] = None) -> List[Dict]:
        """Sample articles using various methods."""
        if seed is not None:
            random.seed(seed)
        
        if method == 'random':
            return random.sample(articles, min(sample_size, len(articles)))
        elif method == 'first':
            return articles[:min(sample_size, len(articles))]
        elif method == 'last':
            return articles[-min(sample_size, len(articles)):]
        elif method == 'indices':
            if indices is None:
                raise ValueError("Indices must be provided when method='indices'")
            return [articles[i] for i in indices if 0 <= i < len(articles)]
        else:
            raise ValueError(f"Unknown sampling method: {method}")
    
    def find_article_by_id(self, article_id: str, enhanced_articles: Optional[List[Dict]] = None) -> Optional[Dict]:
        """Find a specific article by its ID."""
        if enhanced_articles is None:
            enhanced_articles = self.load_enhanced_articles()
            if enhanced_articles is None:
                return None
        
        for article in enhanced_articles:
            if article.get('an') == article_id:
                return article
        
        return None
    
    @staticmethod
    def _match_article_to_countries(article: Dict, 
                                   search_countries: List[str],
                                   case_sensitive: bool = False,
                                   match_mode: str = 'exact') -> bool:
        """Static method to check if an article matches search criteria."""
        main_country = article.get('llm_main_country', '')
        other_countries = article.get('llm_other_countries', [])
        
        # Fast path: if no countries at all
        if not main_country and not other_countries:
            return False
        
        # Build article countries list
        article_countries = []
        if main_country:
            article_countries.append(main_country)
        if other_countries:
            article_countries.extend(other_countries)
        
        # Normalize article countries based on case sensitivity
        if case_sensitive:
            normalized_article_countries = article_countries
        else:
            normalized_article_countries = [c.lower() for c in article_countries if c]
        
        # Apply matching logic based on mode
        for search_term in search_countries:
            if match_mode == 'exact':
                if search_term in normalized_article_countries:
                    return True
            elif match_mode == 'partial':
                if any(search_term in country for country in normalized_article_countries):
                    return True
            elif match_mode == 'any':
                # Split search term into words and check if any word matches
                search_words = search_term.split()
                for word in search_words:
                    if any(word in country for country in normalized_article_countries):
                        return True
        
        return False

    def search_articles_by_country(self, country: str, enhanced_articles: Optional[List[Dict]] = None,
                                  case_sensitive: bool = False, match_mode: str = 'exact',
                                  multiple_countries: Optional[List[str]] = None) -> List[Dict]:
        """Optimized search for articles mentioning specific country/countries."""
        if enhanced_articles is None:
            enhanced_articles = self.load_enhanced_articles()
            if enhanced_articles is None:
                return []
        
        # Prepare search terms
        if multiple_countries:
            search_countries = multiple_countries
        else:
            search_countries = [country]
        
        # Normalize search terms based on case sensitivity
        if case_sensitive:
            normalized_search_countries = search_countries
        else:
            normalized_search_countries = [c.lower() for c in search_countries]
        
        # Use static method for matching - cleaner and more testable
        matching_articles = [
            article for article in enhanced_articles 
            if self._match_article_to_countries(
                article, 
                normalized_search_countries, 
                case_sensitive, 
                match_mode
            )
        ]
        
        return matching_articles
    
    def search_articles_by_multiple_criteria(self, 
                                           countries: Optional[List[str]] = None,
                                           source_names: Optional[List[str]] = None,
                                           date_range: Optional[Tuple[str, str]] = None,
                                           enhanced_articles: Optional[List[Dict]] = None,
                                           case_sensitive: bool = False) -> List[Dict]:
        """Advanced search with multiple criteria."""
        if enhanced_articles is None:
            enhanced_articles = self.load_enhanced_articles()
            if enhanced_articles is None:
                return []
        
        def article_matches_criteria(article):
            # Country filter
            if countries:
                country_match = False
                main_country = article.get('llm_main_country', '')
                other_countries = article.get('llm_other_countries', [])
                article_countries = [main_country] + other_countries if main_country else other_countries
                
                if not case_sensitive:
                    article_countries = [c.lower() for c in article_countries if c]
                    search_countries = [c.lower() for c in countries]
                else:
                    search_countries = countries
                
                for search_country in search_countries:
                    if search_country in article_countries:
                        country_match = True
                        break
                
                if not country_match:
                    return False
            
            # Source name filter
            if source_names:
                article_source = article.get('source_name', '')
                if not case_sensitive:
                    article_source = article_source.lower()
                    search_sources = [s.lower() for s in source_names]
                else:
                    search_sources = source_names
                
                if article_source not in search_sources:
                    return False
            
            # Date range filter
            if date_range:
                article_date = article.get('publication_date', '')
                if article_date:
                    try:
                        # Assuming date format is YYYY-MM-DD or similar
                        if date_range[0] and article_date < date_range[0]:
                            return False
                        if date_range[1] and article_date > date_range[1]:
                            return False
                    except (ValueError, TypeError):
                        # Skip date comparison if format is unexpected
                        pass
            
            return True
        
        return [article for article in enhanced_articles if article_matches_criteria(article)]
    
    def get_country_statistics(self, enhanced_articles: Optional[List[Dict]] = None) -> Dict:
        """Get statistics about country distribution in the dataset."""
        if enhanced_articles is None:
            enhanced_articles = self.load_enhanced_articles()
            if enhanced_articles is None:
                return {}
        
        main_countries = [a.get('llm_main_country') for a in enhanced_articles if a.get('llm_main_country')]
        main_country_counts = Counter(main_countries)
        
        all_countries = []
        for article in enhanced_articles:
            main_country = article.get('llm_main_country')
            other_countries = article.get('llm_other_countries', [])
            
            if main_country:
                all_countries.append(main_country)
            for country in other_countries:
                if country:
                    all_countries.append(country)
        
        all_country_counts = Counter(all_countries)
        
        # Calculate statistics
        total_articles = len(enhanced_articles)
        articles_with_countries = len([a for a in enhanced_articles if a.get('llm_main_country')])
        articles_with_multiple_countries = len([a for a in enhanced_articles 
                                              if a.get('llm_main_country') and a.get('llm_other_countries')])
        
        return {
            'total_articles': total_articles,
            'articles_with_countries': articles_with_countries,
            'coverage_rate': (articles_with_countries / total_articles) * 100 if total_articles > 0 else 0,
            'articles_with_multiple_countries': articles_with_multiple_countries,
            'multi_country_rate': (articles_with_multiple_countries / total_articles) * 100 if total_articles > 0 else 0,
            'main_country_counts': dict(main_country_counts.most_common()),
            'all_country_counts': dict(all_country_counts.most_common()),
            'unique_main_countries': len(main_country_counts),
            'unique_all_countries': len(all_country_counts)
        }
    
    def display_country_statistics(self, stats: Dict) -> None:
        """Display country statistics in a formatted way."""
        print(f"📊 Country Statistics")
        print("=" * 50)
        print(f"Total articles: {stats['total_articles']:,}")
        print(f"Articles with countries: {stats['articles_with_countries']:,} ({stats['coverage_rate']:.1f}%)")
        print(f"Articles with multiple countries: {stats['articles_with_multiple_countries']:,} ({stats['multi_country_rate']:.1f}%)")
        print(f"Unique main countries: {stats['unique_main_countries']:,}")
        print(f"Unique all countries: {stats['unique_all_countries']:,}")
        
        print(f"\nTop 10 main countries:")
        for i, (country, count) in enumerate(list(stats['main_country_counts'].items())[:10], 1):
            percentage = (count / stats['total_articles']) * 100
            print(f"   {country}: {count:,} articles ({percentage:.1f}%)")

def main(raw_data_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/2025/",
         llm_results_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/results/",
         output_dir: str = "/ephemeral/home/xiong/data/Fund/Factiva_News/enhanced/"):
    """Main command-line interface with default paths as arguments."""
    parser = argparse.ArgumentParser(description="LLM Results Merger and Analyzer")
    parser.add_argument("--raw-data-dir", type=str, default=raw_data_dir,
                       help="Directory containing raw data files")
    parser.add_argument("--llm-results-dir", type=str, default=llm_results_dir,
                       help="Directory containing LLM results files")
    parser.add_argument("--output-dir", type=str, default=output_dir,
                       help="Directory for enhanced output files")
    
    # Actions
    parser.add_argument("--merge-all", action="store_true",
                       help="Merge all file pairs")
    parser.add_argument("--search-country", type=str,
                       help="Search for articles mentioning a specific country")
    parser.add_argument("--search-multiple-countries", nargs='+',
                       help="Search for articles mentioning any of multiple countries")
    parser.add_argument("--get-stats", action="store_true",
                       help="Get and display country statistics")
    parser.add_argument("--find-article", type=str,
                       help="Find article by ID")
    
    # Search options
    parser.add_argument("--limit", type=int, default=10,
                       help="Limit number of results to display")
    parser.add_argument("--case-sensitive", action="store_true",
                       help="Use case-sensitive search")
    parser.add_argument("--match-mode", choices=['exact', 'partial', 'any'], default='exact',
                       help="Search matching mode: exact, partial (substring), or any (word match)")
    parser.add_argument("--source-filter", nargs='+',
                       help="Filter by source names")
    parser.add_argument("--date-range", nargs=2, metavar=('START', 'END'),
                       help="Filter by date range (YYYY-MM-DD format)")
    
    args = parser.parse_args()
    
    if args.merge_all:
        merger = LLMResultsMerger(args.raw_data_dir, args.llm_results_dir, args.output_dir)
        stats = merger.process_all_file_pairs()
        
        # Print summary
        if stats:
            total_articles = sum(s['total_raw_articles'] for s in stats)
            total_merges = sum(s['successful_merges'] for s in stats)
            overall_rate = (total_merges / total_articles) * 100 if total_articles > 0 else 0
            print(f"\n✅ MERGE COMPLETE")
            print(f"Total articles: {total_articles:,}")
            print(f"Successful merges: {total_merges:,}")
            print(f"Overall success rate: {overall_rate:.1f}%")
    
    if any([args.search_country, args.search_multiple_countries, args.get_stats, 
            args.find_article]):
        analyzer = LLMResultsAnalyzer(args.output_dir)
        
        if args.search_country or args.search_multiple_countries:
            import time
            start_time = time.time()
            
            if args.search_multiple_countries:
                articles = analyzer.search_articles_by_country(
                    country="",  # Ignored when multiple_countries is provided
                    multiple_countries=args.search_multiple_countries,
                    case_sensitive=args.case_sensitive,
                    match_mode=args.match_mode
                )
                search_term = f"[{', '.join(args.search_multiple_countries)}]"
            else:
                articles = analyzer.search_articles_by_country(
                    args.search_country,
                    case_sensitive=args.case_sensitive,
                    match_mode=args.match_mode
                )
                search_term = args.search_country
            
            search_time = time.time() - start_time
            
            print(f"🔍 Found {len(articles)} articles mentioning {search_term}")
            print(f"⏱️  Search completed in {search_time:.3f} seconds ({args.match_mode} mode)")
            
            for i, article in enumerate(articles[:args.limit], 1):
                print(f"[{i}] {article.get('an', 'N/A')} - {article.get('title', 'N/A')[:80]}...")
                print(f"    Countries: {article.get('llm_main_country', 'N/A')} + {article.get('llm_other_countries', [])}")
                print(f"    Source: {article.get('source_name', 'N/A')}")
            
            if len(articles) > args.limit:
                print(f"... and {len(articles) - args.limit} more articles")
        
        if args.get_stats:
            stats = analyzer.get_country_statistics()
            analyzer.display_country_statistics(stats)
        
        if args.find_article:
            article = analyzer.find_article_by_id(args.find_article)
            if article:
                print(f"✅ Found article: {article.get('title', 'N/A')}")
                print(f"Main Country: {article.get('llm_main_country', 'N/A')}")
                print(f"Other Countries: {article.get('llm_other_countries', [])}")
                print(f"Source: {article.get('source_name', 'N/A')}")
                print(f"Publication Date: {article.get('publication_date', 'N/A')}")
            else:
                print(f"❌ Article with ID '{args.find_article}' not found")
    
    if not any([args.merge_all, args.search_country, args.search_multiple_countries, 
                args.get_stats, args.find_article]):
        parser.print_help()

if __name__ == "__main__":
    main() 
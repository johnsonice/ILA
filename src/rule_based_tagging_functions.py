#%%
"""
Rule-based tagging transformation functions for article processing.

This module contains various transformation functions that can be applied
to article dictionaries for data preprocessing and feature extraction.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Callable, Any
import re

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from libs.meta_utils import tag_country
from libs.country_dict_full import get_dict
from libs.meta_utils import construct_country_group_rex
from functools import partial


def transform_dates(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform date/datetime fields from timestamps to readable format.
    
    Parameters:
        article (dict): Article dictionary containing potential date fields.
        
    Returns:
        dict: Article with transformed date fields.
    """
    if not isinstance(article, dict):
        return article
        
    date_patterns = {
        'date', 'datetime', 'time', 'timestamp', 'created', 'modified', 
        'published', 'ingestion', 'publication', 'modification'
    }
    
    # Create a copy to avoid modifying the original
    article_copy = article.copy()
    
    for key, value in article_copy.items():
        if (any(p in key.lower() for p in date_patterns) and 
            isinstance(value, str) and value.isdigit()):
            try:
                # Handle both millisecond (13 digits) and second (10 digits) timestamps
                ts = int(value) / (1000 if len(value) == 13 else 1)
                article_copy[key] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, OSError):
                # Keep original value if conversion fails
                continue
                
    return article_copy


def create_country_tagging(article: Dict[str, Any],country_rex_dict: Dict = None) -> Callable:
    """
    Factory function to create a country tagging function.
    
    Parameters:
        country_rex_dict (dict, optional): Dictionary of regex patterns for countries.
                                         If None, will be generated from default country dict.
    
    Returns:
        callable: Function that tags countries in articles.
    """
    if country_rex_dict is None:
        country_dict = get_dict()
        country_rex_dict = construct_country_group_rex(country_dict)
    
    if not isinstance(article, dict):
        return article
    
    # Create a copy to avoid modifying the original
    article_copy = article.copy()
    
    try:
        country_tags = list(tag_country(article_copy, country_rex_dict))
        article_copy['ILA_RulebasedCountryTag'] = country_tags
    except Exception as e:
        print(f"Warning: Country tagging failed for article: {e}")
        article_copy['ILA_RulebasedCountryTag'] = []
        
    return article_copy 
    
  

def extract_text_length(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract text length statistics for various text fields.
    
    Parameters:
        article (dict): Article dictionary.
        
    Returns:
        dict: Article with text length fields added.
    """
    if not isinstance(article, dict):
        return article
        
    article_copy = article.copy()
    text_fields = ['title', 'body', 'snippet', 'content', 'text']

    # Concatenate all available text fields into one string
    combined_text = ' '.join(
        str(article_copy[field])
        for field in text_fields
        if field in article_copy and isinstance(article_copy[field], str)
    )
    # Default to zero when no text present
    word_count = 0
    sentence_count = 0

    if combined_text.strip():
        # Compute word count
        word_count = len(combined_text.split())
        # Compute sentence count using regex split on common sentence delimiters
        sentence_count = len([s for s in re.split(r'[.!?]', combined_text) if s.strip()])

    # Store aggregated metrics following the ILA_ naming convention
    article_copy['ILA_WordCount'] = word_count
    article_copy['ILA_SentenceCount'] = sentence_count

    return article_copy

class TradeTopicTagger:
    def __init__(self):
        # Define the list of trade-related keywords (with regex for plural/singular variants)
        self.keywords = [
            # Basic trade terms
            r"import(?:s|ing)?", r"export(?:s|ing)?", r"export(?:ing)? market(?:s)?", r"export competitiven(?:ess)?",
            r"importing", r"exporting", r"trading", r"trade(?:s|d|ing)?", r"commerce", r"global trade", r"import licence(?:s)?",
            r"goods trade", r"service(?:s)? trade", r"services trade", r"GTA",

            # Tariffs and duties
            r"tariff(?:s)?", r"tariff(?:s)? hike", r"tariff(?:s)? increase", r"tariff(?:s)? cut",
            r"tariff(?:s)? exemption", r"retaliatory tariff(?:s)?", r"tariff quota(?:s)?", r"tariff binding",
            r"ad valorem tariff(?:s)?", r"border tax adjustment", r"countervailing dut(?:y|ies)?",
            r"customs dut(?:y|ies)", r"custom duties", r"import dut(?:y|ies)", r"export dut(?:y|ies)", r"import tax(?:e|es)?", 
            r"countervailing", r"countervailing duty",

            # Trade agreements
            r"free trade agreement(?:s)?", r"bilateral trade agreement(?:s)?", r"multilateral trade agreement(?:s)?",
            r"preferential trade agreement(?:s)?", r"regional trade agreement(?:s)?", r"trade treaty(?:ies)?",
            r"trade agreement(?:s)?", r"FTA(?:s)?", r"NAFTA", r"CUSMA", r"USMCA", r"CAFTA",

            # Institutions and mechanisms
            r"WTO(?: dispute| ruling| panel)?", r"WTO negotiation(?:s)?", r"World Trade Organization",
            r"wto dispute", r"GATT", r"Doha round", r"Uruguay round",

            # Barriers and restrictions
            r"non-tariff barrier(?:s)?", r"non-tariff measure(?:s)?", r"nontariff measure(?:s)?",
            r"technical trade barrier(?:s)?", r"import ban(?:s)?", r"export ban(?:s)?",
            r"export barrier(?:s)?", r"import barrier(?:s)?", r"trade embargo(?:es)?", r"quotas?",
            r"import quota(?:s)?", r"export quota(?:s)?", r"binding quota(?:s)?", r"non-binding quota(?:s)?",
            r"safeguard measure(?:s)?", r"rules of origin", r"local content", r"local content requirement(?:s)?",
            r"voluntary export restraint(?:s)?", r"voluntary export", r"voluntary export restraint arrangements",
            r"voluntary import expansion", r"tariff quota", r"trade-related investment measure(?:s)?",
            r"export credits?", r"export control(?:s)?", r"customs (?:procedure|reform|clearance)",
            r"customs enforcement",

            # Trade policy
            r"foreign trade policy", r"trade policy", r"trade policy uncertainty", r"uncertain trade environment",
            r"protectionist polic(?:y|ies)", r"liberalization polic(?:y|ies)?", r"trade liberalization",
            r"policy reversal(?:s)?", r"policy backtracking", r"trade spillover(?:s)?",

            # Supply chains and logistics
            r"supply chain(?: disruption(?:s)?| shock(?:s)?| bottleneck(?:s)?| resilience| pressure(?:s)?)?",
            r"supply[- ]chain(?: disruption(?:s)?| shock(?:s)?| bottleneck(?:s)?| resilience| pressure(?:s)?)?",
            r"global value chain(?:s)?", r"GVC(?:s)?", r"port congestion", r"shipping delay(?:s)?",
            r"container shortage(?:s)?", r"logistics disruption(?:s)?", r"reshoring", r"nearshoring",
            r"friend-shoring", r"cargo",

            # Geopolitical factors
            r"geopolitical tension(?:s)?", r"geopolitical shock(?:s)?", r"geopolitical concern(?:s)?",
            r"geopolitical fragmentation", r"geo-economic fragmentation", r"geoeconomic fragmentation",
            r"geoeconomic", r"geopolitical", r"geopolitics", r"economic fragmentation",
            r"strategic competitiveness", r"economic coercion", r"trade war(?:s)?", r"trade tension(?:s)?",
            r"trade disruption(?:s)?", r"fragmented trade",

            # External sector
            r"external sector", r"FX intervention(?:s)?", r"foreign exchange intervention(?:s)?",
            r"foreign exchange market", r"foreign exchange polic(?:y|ies)?",
            r"international reserve(?:s)?", r"foreign exchange reserve(?:s)?", r"foreign asset(?:s)?",
            r"real exchange rate", r"current account",

            # Other macro indicators
            r"commodity price (?:shock|surge)", r"commodity export ban(?:s)?",
            r"trade balance", r"trade deficit", r"net-commodity-importing", r"FDI measures",
        ]

        # Compile regex pattern once for performance
        self.pattern = re.compile(r"(?:{})".format("|".join(self.keywords)), flags=re.IGNORECASE)

    def tag(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Tag an article with trade-related content."""
        if not isinstance(article, dict):
            return article
        article_copy = article.copy()
        
        search_content = ' '.join([
            article_copy.get('title', ''),
            article_copy.get('snippet', ''),
            '.'.join(article_copy.get('body', '.').split('.')[:5])
        ]).lower()
        
        matches = self.pattern.findall(search_content)
        unique_matches = list(set(matches))
        article_copy['ILA_TradeTopicTag'] = bool(matches)
        article_copy['ILA_TradeTopicKeywords'] = unique_matches
        article_copy['ILA_TradeTopicKeywordCount'] = len(unique_matches)
        
        return article_copy

#%%
if __name__ == "__main__":
    import json
    sample_file = "/ephemeral/home/xiong/data/Fund/Factiva_News/2025/2025_articles_1.json"
    with open(sample_file, 'r') as f:
        articles = json.load(f)
    
    country_dict = get_dict()
    country_rex_dict = construct_country_group_rex(country_dict)
    trade_topic_tagger = TradeTopicTagger()
    
    for article_copy in articles[:1000]:
        article_copy = create_country_tagging(article_copy,country_rex_dict)
        article_copy = extract_text_length(article_copy)
        article_copy = transform_dates(article_copy)
        article_copy = trade_topic_tagger.tag(article_copy)
    
    print("ILA_RulebasedCountryTag: ", article_copy['ILA_RulebasedCountryTag'])
    print("ILA_WordCount: ", article_copy['ILA_WordCount'])
    print("ILA_SentenceCount: ", article_copy['ILA_SentenceCount'])
    print("publication_date: ", article_copy['publication_date'])
    print("ILA_TradeTopicTag: ", article_copy['ILA_TradeTopicTag'])
    print("ILA_TradeTopicKeywords: ", article_copy['ILA_TradeTopicKeywords'])   
    print("ILA_TradeTopicKeywordCount: ", article_copy['ILA_TradeTopicKeywordCount'])
#%%    
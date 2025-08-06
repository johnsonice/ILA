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
sys.path.append(str(Path(__file__).parent.parent.parent))
import time

# # Enable progress bars for swifter and tqdm
# tqdm.pandas()
# swifter.config.progress_bar = True

class TPUDetector:
    def __init__(self):
        # Compile regex for trade-related terms
        self.trade_terms = re.compile(
            r"(USMCA|NAFTA|CUSMA|WTO|World Trade Organization|GATT|General Agreement on Tariffs and Trade|"
            r"Doha Round|Uruguay Round|trade polic(?:y|ies)|trade agreement(?:s)?|free trade(?: agreement(?:s)?)?|"
            r"FTA(?:s)?|preferential trade|bilateral trade|multilateral trade|trade negotiation(?:s)?|"
            r"trade act(?:s)?|trade treat(?:y|ies)|trade rule(?:s)?|trade friction(?:s)?|market access|"
            r"tariff(?:s)?|retaliatory tariff(?:s)?|retaliation|import tariff(?:s)?|export tariff(?:s)?|"
            r"tariff dut(?:y|ies)|custom(?:s)? dut(?:y|ies)|duty on import(?:s)?|import dut(?:y|ies)|"
            r"import barrier(?:s)?|import restriction(?:s)?|import liberalization|export restriction(?:s)?|"
            r"export subsid(?:y|ies)|\b(import|imports|imported|importing)\b|\b(export|exports|exported|exporting)\b|"
            r"border(?:s)?|trade barrier(?:s)?|non-tariff barrier(?:s)?|trade remed(?:y|ies)|"
            r"countervailing dut(?:y|ies)|trade dispute(?:s)?|trade panel(?:s)?|WTO ruling(?:s)?|"
            r"trade tribunal(?:s)?|trade retaliation(?:s)?|trade sanction(?:s)?|trade enforcement|protectionism|"
            r"unilateralism|trade liberalization|international trade|import (ban|tax|subsid)(?:es)?|"
            r"export (ban|tax|subsid)(?:es)?|border (ban|tax|subsid)(?:es)?|trade facilitation|escalating trade|"
            r"trade partnership(?:s)?|trade adjustment assistance|customs tariff(?:s)?|tariff preference(?:s)?|"
            r"trade restriction(?:s)?|trade embargo(?:es)?|import surcharge(?:s)?|sectoral tariff(?:s)?|"
            r"preferential tariff(?:s)?|reciprocal tariff(?:s)?|customs valuation rule(?:s)?|"
            r"import licensing requirement(?:s)?|rules of origin restriction(?:s)?|export control(?:s)?|"
            r"trade tax(?:es)?|import protection|protectionist barrier(?:s)?|plurilateral(?:s)?|"
            r"subsidies and countervailing measures|trade-restrictive|trade-facilitating|strategic tariff(?:s)?|"
            r"GATT ruling(?:s)?|WTO panel(?:s)?|GATT panel(?:s)?|WTO case(?:s)?|trade war(?:s)?|"
            r"customs union(?:s)?|anti-dumping)",
            flags=re.IGNORECASE
        )

        # Compile regex for uncertainty-related terms
        self.uncertainty_terms = re.compile(
            r"(uncertain(?:ty|ties)?|unpredictabl(?:e|ility)?|volatil(?:e|ity)|downside risk|upside risk|unexpected|"
            r"unknown|crisis|crises|war|unclear|tension(?:s)?|danger(?:s)?|fear(?:s)?|concern(?:s|ed| about)?|"
            r"caution|worr(?:y|ies)?|anxious|anxiety|unease|unstabl(?:e|ity)|threat(?:s)?|threaten(?:s|ed|ing)?|"
            r"ambiguous|ambiguity|imprecise|vague|unresolved|unanticipated|unforeseen|hesitant|hesitation|"
            r"doubt(?:ful|s)?|skeptic(?:al|ism)?|murky|precarious|tentative|fluid|chang(?:eable|ing)|shifting|"
            r"wavering|turmoil|turbulent|turbulence|fragil(?:e|ity)|fluctuation(?:s)?|slowdown|downturn|"
            r"depression|recession(?:ary)?|pessimism|pessimistic|stagflation|erosion|deterioration|meltdown|"
            r"bubble burst|stress(?:ed)?|distress|vulnerab(?:le|ility|ilities)?|apprehensive|possibilit(?:y|ies)?|"
            r"likelihood|probabilit(?:y|ies)?|prospect(?:s)?|potential|speculat(?:ion|ive)|rumor(?:s)?|"
            r"rumours?|bleak|gloom|nervousness|cautious|wary|unconfirmed|pressure(?:s)?|confusion|"
            r"challenge\w*|dispute(?:s)?|issue(?:s)?|dubious)",
            flags=re.IGNORECASE
        )
        
        self.tpu_pattern = re.compile(
            rf"\b({self.trade_terms.pattern})\b(?:\W+\w+){{0,10}}?\W+\b({self.uncertainty_terms.pattern})\b|"
            rf"\b({self.uncertainty_terms.pattern})\b(?:\W+\w+){{0,10}}?\W+\b({self.trade_terms.pattern})\b",
            flags=re.IGNORECASE
        )

    def normalize_text_preserving_acronyms(self, text: str) -> str:
        """Clean text by removing punctuation and lowering case, while preserving acronyms (e.g., IMF, WTO)."""
        if not isinstance(text, str):
            return ""
        # Identify acronyms (e.g., IMF, WTO) and temporarily replace them
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        for i, ac in enumerate(acronyms):
            text = text.replace(ac, f"__ACRO_{i}__")
        text = re.sub(r"[^\w\s]", " ", text).lower()
        for i, ac in enumerate(acronyms):
            text = text.replace(f"__acro_{i}__", ac)
        return text

    def detect_tpu(self, text: str) -> bool:
        """Return True if both trade and uncertainty terms co-occur within a 10-word window."""
        return bool(self.tpu_pattern.search(str(text)))
    
    def tag(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Tag an article with TPU detection."""
        if not isinstance(article, dict):
            return article
        article_copy = article.copy()
        text_content = ' '.join([
            article_copy.get('title', ''),
            article_copy.get('snippet', ''),
            '.'.join(article_copy.get('body', '.').split('.')[:5])
        ]).lower()
        
        # Normalize text while preserving acronyms
        normalized_text = self.normalize_text_preserving_acronyms(text_content)
        
        # Detect TPU
        tpu_flag = self.detect_tpu(normalized_text)
        
        article_copy['ILA_TPU_Flag'] = tpu_flag
        if tpu_flag:
            tpu_reference_content = article_copy.get('title', '') + ' ' + article_copy.get('snippet', '') 
            if len(tpu_reference_content) <10:
                # If title and snippet are too short, use the first few sentences of the body
                tpu_reference_content += ' ' + '.'.join(article_copy.get('body', '').split('.')[:5])
            article_copy['ILA_TPU_Reference'] = tpu_reference_content[:500]  # Limit to 500 characters
        else:
            article_copy['ILA_TPU_Reference'] = ''
        
        return article_copy

    # def apply_to_dataframe(self, df: pd.DataFrame, text_column: str = "body") -> pd.DataFrame:
    #     """Clean the text column, apply TPU detection, and return updated DataFrame."""
    #     df = df.copy()
    #     df[text_column] = df[text_column].fillna('')
    #     df["body_clean"] = df[text_column].apply(self.normalize_text_preserving_acronyms)

    #     print("Running TPU detection with swifter...")
    #     start = time.time()
    #     df["tpu_flag"] = df["body_clean"].swifter.apply(self.detect_tpu).astype(int)
    #     print(f"Completed in {round(time.time() - start, 2)} seconds.")
    #     return df

#%%
if __name__ == "__main__":
    import json
    #sample_file = "/ephemeral/home/xiong/data/Fund/Factiva_News/2025/2025_articles_1.json"
    sample_file = "//data2/CommercialData/Factiva_Repository/2025/2025_articles_1.json"
    with open(sample_file, 'r') as f:
        articles = json.load(f)
    TPU_tagger = TPUDetector()
    for article_copy in articles[:1000]:
        article_copy = TPU_tagger.tag(article_copy)
        if article_copy['ILA_TPU_Flag']:
            print("TPU detected in article:")
            print("Title: ", article_copy.get('title', ''))
            print("Snippet: ", article_copy.get('snippet', ''))
            print("Body: ", article_copy.get('body', '')[:200])


#%%    
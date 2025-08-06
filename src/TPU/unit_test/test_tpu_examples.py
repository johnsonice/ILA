"""
Test examples for the TPU (Trade Policy Uncertainty) detection function.

This script provides various example sentences to test the detect_tpu function
and demonstrates different scenarios where TPU should or should not be detected.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from TPU_tagging_functions import TPUDetector

def test_tpu_detection():
    """Test the TPU detection function with various example sentences."""
    
    # Initialize the TPU detector
    detector = TPUDetector()
    
    # Test cases where TPU SHOULD be detected (trade + uncertainty within 10 words)
    positive_examples = [
        # Direct trade-uncertainty combinations
        "The trade war has created significant uncertainty in global markets.",
        "Import tariffs may cause unpredictable economic volatility.",
        "WTO disputes have led to concerns about future trade policies.",
        "NAFTA renegotiation brings unknown risks to manufacturers.",
        "Trade tensions are causing worry among investors.",
        "The uncertain trade agreement negotiations continue.",
        "Escalating trade conflicts threaten market stability.",
        "Tariff uncertainty is affecting business planning.",
        "Export restrictions create doubt about supply chains.",
        "Trade policy changes bring unexpected challenges.",
        
        # Longer sentences with trade and uncertainty within 10-word window
        "The government announced new tariff policies that created market uncertainty.",
        "Companies are facing unprecedented challenges due to volatile trade regulations.",
        "Import duties announced yesterday have caused significant investor concerns.",
        "The bilateral trade negotiations remain unclear and unpredictable.",
        "Free trade agreement talks are shrouded in ambiguity and doubt.",
        
        # With acronyms
        "WTO rulings have introduced regulatory uncertainty across industries.",
        "USMCA implementation faces unclear timelines and potential risks.",
        "FTA negotiations remain tentative and subject to political volatility.",
        
        # Reverse order (uncertainty then trade)
        "Market volatility stems from ongoing trade disputes.",
        "Economic uncertainty follows new import restrictions.",
        "Political tensions affect bilateral trade agreements significantly.",
        "Crisis management includes emergency trade policy measures.",
        "Unknown factors influence export subsidy decisions."
    ]
    
    # Test cases where TPU should NOT be detected
    negative_examples = [
        # Only trade terms
        "The trade agreement was successfully negotiated.",
        "Import volumes increased by 15% this quarter.",
        "WTO members agreed on new trade rules.",
        "Export subsidies support domestic manufacturers.",
        "Tariff rates were reduced across all sectors.",
        
        # Only uncertainty terms
        "The stock market showed significant volatility.",
        "Economic uncertainty affects consumer spending.",
        "Political tensions rise amid election concerns.",
        "Market crisis requires immediate intervention.",
        "Unknown factors influence investment decisions.",
        
        # Trade and uncertainty terms too far apart (>10 words)
        "The comprehensive bilateral trade agreement between the United States and European Union creates significant uncertainty for domestic manufacturers.",
        "Import restrictions implemented by the government last year have now begun to cause widespread economic uncertainty.",
        "Trade policy experts believe that the current geopolitical environment will continue to generate market volatility.",
        
        # General business/economic content without TPU
        "The company reported strong quarterly earnings.",
        "Technology stocks gained 3% in morning trading.",
        "Central bank maintains current interest rates.",
        "GDP growth exceeded expectations this quarter.",
        "Employment rates show steady improvement trends."
    ]
    
    print("="*80)
    print("TESTING TPU DETECTION FUNCTION")
    print("="*80)
    
    print("\n🟢 POSITIVE EXAMPLES (Should detect TPU):")
    print("-" * 50)
    for i, sentence in enumerate(positive_examples, 1):
        result = detector.detect_tpu(sentence)
        status = "✅ DETECTED" if result else "❌ MISSED"
        print(f"{i:2d}. {status}: {sentence}")
    
    print("\n🔴 NEGATIVE EXAMPLES (Should NOT detect TPU):")
    print("-" * 50)
    for i, sentence in enumerate(negative_examples, 1):
        result = detector.detect_tpu(sentence)
        status = "❌ FALSE POSITIVE" if result else "✅ CORRECT"
        print(f"{i:2d}. {status}: {sentence}")
    
    # Calculate accuracy
    positive_results = [detector.detect_tpu(sentence) for sentence in positive_examples]
    negative_results = [detector.detect_tpu(sentence) for sentence in negative_examples]
    
    true_positives = sum(positive_results)
    false_negatives = len(positive_examples) - true_positives
    true_negatives = len(negative_examples) - sum(negative_results)
    false_positives = sum(negative_results)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    accuracy = (true_positives + true_negatives) / (len(positive_examples) + len(negative_examples))
    
    print("\n📊 PERFORMANCE SUMMARY:")
    print("=" * 50)
    print(f"True Positives:  {true_positives}/{len(positive_examples)}")
    print(f"False Negatives: {false_negatives}/{len(positive_examples)}")
    print(f"True Negatives:  {true_negatives}/{len(negative_examples)}")
    print(f"False Positives: {false_positives}/{len(negative_examples)}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"Accuracy:  {accuracy:.2%}")

def test_edge_cases():
    """Test edge cases and special scenarios."""
    
    detector = TPUDetector()
    
    edge_cases = [
        # Empty/None inputs
        ("", "Empty string"),
        (None, "None input"),
        
        # Very short text
        ("Trade uncertainty", "Very short text"),
        
        # Punctuation heavy
        ("Trade, uncertainty... concerns!!! volatility.", "Heavy punctuation"),
        
        # Case sensitivity
        ("TRADE WAR CREATES UNCERTAINTY", "All caps"),
        ("trade war creates uncertainty", "All lowercase"),
        
        # Numbers and special characters
        ("Trade war 2024 creates $100M uncertainty", "With numbers and symbols"),
        
        # Multiple matches
        ("Trade disputes cause uncertainty while tariff wars create volatility", "Multiple TPU instances"),
        
        # Acronyms preservation
        ("WTO rulings create IMF concerns about FTA uncertainty", "Multiple acronyms"),
    ]
    
    print("\n🔍 EDGE CASE TESTING:")
    print("=" * 50)
    
    for text, description in edge_cases:
        try:
            result = detector.detect_tpu(text)
            print(f"✅ {description}: {result} - '{text}'")
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")

if __name__ == "__main__":
    test_tpu_detection()
    test_edge_cases()

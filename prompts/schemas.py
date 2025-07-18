
from typing import List, Optional, Dict, Type
from pydantic import BaseModel, Field

class CountryIdentificationResponse(BaseModel):
    main_country: str = Field(
        default="",
        description="The single primary country identified in the article; Follow IMF country name conventions. Use English only.",
        max_length=50
    )
    other_countries: List[str] = Field(
        default_factory=list,
        description="A de‑duplicated list of other countries mentioned in the article; Follow IMF country name conventions. Must contain fewer than 6 countries.",
        max_length=100
    )
class SentimentAnalysisResponse(BaseModel):
    """Schema for sentiment analysis prompts (basic, chain-of-thought, few-shot)."""
    sentiment_label: str = Field(
        ...,
        description="One of: strong negative, moderate negative, neutral, moderate positive, strong positive.",
        max_length=50,
    )
    tone_score: float = Field(
        ...,
        description="Continuous score between -5.0 (strongly negative) and 5.0 (strongly positive).",
        ge=-5.0,
        le=5.0,
    )
    justification: str = Field(
        ...,
        description="Brief explanation of key phrases that influenced the sentiment decision.",
        max_length=1000,
    )
class TenseExtractionResponse(BaseModel):
    """Schema for tense_extraction prompt."""
    tense: str = Field(
        ...,
        description="Temporal context of the sentence: Past, Present, or Future.",
        pattern="^(Past|Present|Future)$",
        max_length=20,
    )
class ProductCategoriesResponse(BaseModel):
    """Schema for product_categories prompt."""
    result: List[str] = Field(
        default_factory=list,
        description="List of product categories identified (e.g., Medical Products, Semiconductors).",
    )
class StatedMotiveResponse(BaseModel):
    """Schema for stated_motive prompt."""
    result: List[str] = Field(
        default_factory=list,
        description="List of stated motives for the policy intervention.",
    )
class BroadPolicyCategoriesResponse(BaseModel):
    """Schema for broad_policy_categories prompt."""
    result: List[str] = Field(
        default_factory=list,
        description="List of broad policy instrument categories that apply.",
    )
class MeasureNatureResponse(BaseModel):
    """Schema for measure_nature prompt."""
    result: str = Field(
        ...,
        description="Nature of the measure: Liberalising, Distortive, or Other.",
        pattern="^(Liberalising|Distortive|Other)$",
        max_length=40,
    )
class TimelineExtractionResponse(BaseModel):
    """Schema for timeline_extraction prompt."""

    announcement_date: str = Field(
        ...,
        description="Free-text representation of the announcement date or 'Not applicable'.",
        max_length=100,
    )
    implementation_date: str = Field(
        ...,
        description="Free-text representation of the implementation date or 'Not applicable'.",
        max_length=100,
    )
    removal_date: str = Field(
        ...,
        description="Free-text representation of the removal/end date or 'Not applicable'.",
        max_length=100,
    )
class InterventionTypeResponse(BaseModel):
    """Schema for intervention_type prompt."""

    result: List[str] = Field(
        default_factory=list,
        description="List of intervention type descriptors present in the sentence.",
    )


# -----------------------------------------------------------------------------
# Registry mapping each prompt template name to its Markdown file and schema.
# -----------------------------------------------------------------------------

PROMPT_REGISTRY: Dict[str, Dict[str, object]] = {
    "country_identification": {
        "prompt_file": "extract_country_name.md",
        "response_model": CountryIdentificationResponse,
    },
    "sentiment_analysis_basic": {
        "prompt_file": "sentiment_analysis_basic.md",
        "response_model": SentimentAnalysisResponse,
    },
    "sentiment_analysis_chain_of_thought": {
        "prompt_file": "sentiment_analysis_cot.md",
        "response_model": SentimentAnalysisResponse,
    },
    "sentiment_analysis_few_shot": {
        "prompt_file": "sentiment_analysis_few_shot.md",
        "response_model": SentimentAnalysisResponse,
    },
    "tense_extraction": {
        "prompt_file": "tense_extraction.md",
        "response_model": TenseExtractionResponse,
    },
    "product_categories": {
        "prompt_file": "product_categories.md",
        "response_model": ProductCategoriesResponse,
    },
    "stated_motive": {
        "prompt_file": "stated_motive.md",
        "response_model": StatedMotiveResponse,
    },
    "broad_policy_categories": {
        "prompt_file": "broad_categories.md",
        "response_model": BroadPolicyCategoriesResponse,
    },
    "measure_nature": {
        "prompt_file": "measure_nature.md",
        "response_model": MeasureNatureResponse,
    },
    "timeline_extraction": {
        "prompt_file": "timeline.md",
        "response_model": TimelineExtractionResponse,
    },
    "intervention_type": {
        "prompt_file": "intervention_type.md",
        "response_model": InterventionTypeResponse,
    },
}
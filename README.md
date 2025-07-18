# ILA – Intelligent Language Agents for IMF Surveillance

ILA (Intelligent Language Agents) is a lightweight GenAI toolkit that helps IMF economists and analysts turn raw text (news articles, reports, social-media posts, …) into machine-readable signals in minutes – not weeks.

The repo bundles reusable libraries, prompt templates, and ready-made pipelines so you can:

* 🔌 Query a variety of Large Language Models (LLMs) through one unified interface (OpenAI, Google Gemini, Anthropic Claude, or any OpenAI-compatible endpoint such as **sgLang**, **Groq**, **Together**, etc.).
* 🗂️ Receive *structured* responses with type guarantees thanks to Pydantic models.
* ⚡ Run thousands of requests **asynchronously** for high-throughput inference or RAG workloads.
* 📄 Manage prompts as markdown files with YAML front-matter – perfect for version-controlling prompt engineering.
* 🛠️ Chain everything together in self-documenting Python pipelines (e.g. country extraction from Factiva news).

---

## Quick tour

| Folder | What lives here |
| ------ | --------------- |
| `libs/` | Core reusable libraries (LLM factories, utilities, prompt helpers) |
| `src/`  | End-to-end pipelines & CLI scripts – e.g. `run_llm_article_level.py` (generic multi-task pipeline) and `extract_country_name.py` (legacy standalone) |
| `prompts/` | Prompt templates **plus** `schemas.py` registry that maps each prompt to a Pydantic response model |
| `examples/` | Minimal, runnable examples – start here if you are new to the codebase |
| `test/` | PyTest suites covering the public API |
| `notebook/` | Jupyter notebooks that illustrate typical workflows |

---

## Installation

```bash
# 1. Create and activate a virtual environment (conda, venv, …)
conda create -n ila python=3.10 -y
conda activate ila

# 2. Install base requirements
pip install -r requirements.txt

# 3. (Optional) Install provider-specific extras
#    Only required if you need that provider.
# pip install google-generativeai   # Google Gemini
# pip install anthropic            # Anthropic Claude
```

Environment variables are loaded from a local `.env` file – create one at the repo root:

```ini
# .env (example)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...      # optional
ANTHROPIC_API_KEY=...   # optional
```

---

## Usage examples

### 1. Unified LLM interface

```python
from libs.llm_factory_general import create_openai_factory

messages = [
    {"role": "user", "content": "Name three countries in South America."}
]

llm = create_openai_factory(model_name="gpt-4o-mini")
print(llm.get_response_content(messages))
```

### 2. Structured outputs

```python
from pydantic import BaseModel, Field
from libs.llm_factory_general import create_openai_factory

class Capital(BaseModel):
    city: str = Field(...)
    country: str

class CapitalsResponse(BaseModel):
    capitals: list[Capital] = Field(default_factory=list)

messages = [
    {"role": "system", "content": "Return JSON strictly following the provided schema."},
    {"role": "user", "content": "Give me two European capitals."},
]

llm = create_openai_factory()
result = llm.get_structured_response(messages, CapitalsResponse)
print(result)
```

### 3. Batch async inference against a local sgLang server

```python
from libs.llm_factory_openai import BatchAsyncLLMAgent
import asyncio

local_model = {
    "model": "Qwen/Qwen3-8B",
    "base_url": "http://localhost:8102/v1",  # sgLang endpoint
    "api_key": "abc",
    "temperature": 0,
}

a = BatchAsyncLLMAgent(**local_model)

async def main():
    await a.test_connection()
    batch = [[{"role": "user", "content": f"Say hi {i}"}] for i in range(5)]
    print(await a.get_batch_response_contents_auto(batch, batch_size=5))

asyncio.run(main())
```

---

## Running the sample pipeline

The script below scans a directory of Factiva JSON dumps, extracts the main country mentioned in each article, and writes the results back to disk.

```bash
python src/extract_country_name.py \
  --data_dir /path/to/factiva/2025 \
  --output_dir /tmp/ila_results \
  --n_jobs 4
```

---

## Built-in tasks (prompt registry)

The file `prompts/schemas.py` maintains a single **source of truth** linking each
Markdown prompt template to its response schema.  The keys below can be passed
to the `--task` flag of the generic pipeline:

| Task ID | Template | Response model |
|---------|----------|----------------|
| `country_identification` | `extract_country_name.md` | `CountryIdentificationResponse` |
| `sentiment_analysis_basic` | `sentiment_analysis_basic.md` | `SentimentAnalysisResponse` |
| `sentiment_analysis_chain_of_thought` | `sentiment_analysis_cot.md` | `SentimentAnalysisResponse` |
| `sentiment_analysis_few_shot` | `sentiment_analysis_few_shot.md` | `SentimentAnalysisResponse` |
| `tense_extraction` | `tense_extraction.md` | `TenseExtractionResponse` |
| `product_categories` | `product_categories.md` | `ProductCategoriesResponse` |
| `stated_motive` | `stated_motive.md` | `StatedMotiveResponse` |
| `broad_policy_categories` | `broad_categories.md` | `BroadPolicyCategoriesResponse` |
| `measure_nature` | `measure_nature.md` | `MeasureNatureResponse` |
| `timeline_extraction` | `timeline.md` | `TimelineExtractionResponse` |
| `intervention_type` | `intervention_type.md` | `InterventionTypeResponse` |

---

## Generic multi-task pipeline

`src/run_llm_article_level.py` is a **single CLI** that can run *any* of the
prompt-schema pairs listed above in batched, asynchronous mode.  It takes care
of loading the template, inserting the article text, enforcing the schema and
writing one JSON result file per input JSON.

Example:

```bash
python src/run_llm_article_level.py \
  --task sentiment_analysis_basic \
  --data_dir /path/to/articles_json/ \
  --output_dir /tmp/ila_results/ \
  --batch_size 64 \
  --max_tokens 1024
```

The script uses `libs.llm_factory_openai.BatchAsyncLLMAgent` under the hood but
can be pointed at **any OpenAI-compatible endpoint** (sgLang, Groq, Together,
local LM Studio, …) by tweaking the `local_model_args` dictionary in the file
or passing environment variables.

---

## Rule-based metadata extraction (optional)

If you just need **quick metadata** such as country mentions or human-readable
dates – without paying for LLM calls – run:

```bash
python src/extract_meta.py \
  --data_dir /path/to/articles_json/ \
  --output_file /tmp/ila_metadata.csv
```

Behind the scenes this leverages regex patterns from `libs/meta_utils.py` and a
comprehensive country dictionary to tag articles at **O(μs)** per document.

---

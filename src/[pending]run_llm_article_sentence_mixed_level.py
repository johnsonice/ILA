#%%
"""Generic LLM-powered information extraction pipeline.

This script is a more generalised version of `extract_country_name.py`.  It
allows you to specify a *task* (e.g. `country_identification`,
`sentiment_analysis_basic`, …) at runtime, and automatically:

1. Retrieves the corresponding prompt template Markdown file from the
   `prompts` folder.
2. Loads the associated Pydantic response model from
   `prompts.schemas.PROMPT_REGISTRY`.
3. Executes batched, asynchronous calls to the configured LLM via
   `BatchAsyncLLMAgent`.
4. Merges the article IDs with their structured model outputs (or error
   placeholders) and stores the results as JSON in `output_dir`.

The result filename is `<original_json_filename>_{task}.json` so that
multiple tasks can be run side-by-side without overwriting each other.

Example usage:

```bash
python run_llm_article_level.py \
    --api_key "<API_Key>" \
    --task_id news_scope_classification \
    --data_dir "//data2/CommercialData/Factiva_Repository" \
    --output_dir "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\data\results" \
    --batch_size 16 \
    --model_args "Q:\DATA\SPRAI\Chengyu Huang\8_Data_Science\Factiva_News_Project\ILA\src\llm_args\netmind_qwen3_8b.json"

```

If `--test` is provided the first 20 articles of the first JSON file are
processed, which is handy for quick smoke tests.
"""

#%%
import json
import os
import sys
import time
import glob
import asyncio
import warnings
from pathlib import Path
from typing import List, Dict, Any, Tuple, Callable, Type
# Set up logger
import logging
logger = logging.getLogger(__name__)
import nest_asyncio

from tqdm import tqdm
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Runtime setup
# ---------------------------------------------------------------------------

warnings.filterwarnings("ignore")
nest_asyncio.apply()

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
LIBS_DIR = PROJECT_ROOT / "libs"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Ensure that **PROJECT_ROOT** is on PYTHONPATH so that the `prompts` package
# (and any other top-level modules inside the project) can be discovered when
# doing `import prompts.​…`.  We still add `LIBS_DIR` to directly access helper
# utilities that are not packaged.
for subdir in (PROJECT_ROOT, LIBS_DIR):
    if str(subdir) not in sys.path:
        sys.path.insert(0, str(subdir))

# ---------------------------------------------------------------------------
# Local imports (resolved after sys.path modification)
# ---------------------------------------------------------------------------
from llm_factory_openai import BatchAsyncLLMAgent  # type: ignore
from prompt_utils import load_prompt, format_messages  # type: ignore
from utils import read_json, filter_unprocessed_files  # type: ignore
from prompts.schemas import PROMPT_REGISTRY  # noqa: E402  (after path tweaks)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _build_batch_messages_from_articles(
    articles: List[Dict[str, Any]],
    prompt_template: Dict[str, str],
    *,
    max_article_length: int = 2000,
) -> Tuple[List[List[Dict[str, str]]], List[str]]:
    """Convert a list of article dicts into LLM-ready message batches.

    Each article is condensed into a single string comprising its title,
    snippet and body.  The resulting text is *in-place* substituted into
    the `{TEXT}` placeholder of the prompt *before* the prompt
    is serialised into OpenAI‐style chat messages via `format_messages()`.

    Returning two aligned lists keeps the function side-effect-free while
    ensuring we can later reattach the model outputs to the original
    article IDs in a deterministic order.
    """
    batch_messages: List[List[Dict[str, str]]] = []
    batch_ids: List[str] = []

    for art in articles:
        text_parts = [str(art.get(k, "")) for k in ("title", "snippet", "body") if art.get(k)]
        article_text = " ".join(text_parts)[:max_article_length]
        article_id = str(art.get("an", "unknown_id"))

        # Inject ARTICLE_CONTENT placeholder and build messages list
        this_template = prompt_template.copy()
        this_template["user"] = this_template["user"].format(TEXT=article_text)
        messages = format_messages(this_template, add_schema=True)

        batch_messages.append(messages)
        batch_ids.append(article_id)

    return batch_messages, batch_ids


async def _process_articles_async(
    agent: BatchAsyncLLMAgent,
    batch_messages: List[List[Dict[str, str]]],
    *,
    response_model: Type[BaseModel],
    batch_size: int = 16,
    max_tokens: int = 2000,
    results_post_process: Callable[[List[Any]], List[Any]] = lambda x: x,
    **kwargs,
) -> List[Any]:
    """Run batched inference and post-process the results."""

    contents = await agent.get_batch_response_contents_auto(
        batch_messages,
        batch_size=batch_size,  # how many chat threads are sent per HTTP request
        max_tokens=max_tokens,  # generation budget per completion
        response_format=response_model,  # Pydantic model enforcing JSON schema
        **kwargs,
    )
    return results_post_process(contents)


def _merge_ids_with_responses(ids: List[str], responses: List[Any]) -> List[Dict[str, Any]]:
    """Attach article IDs to response models or error strings."""

    merged: List[Dict[str, Any]] = []
    for msg_id, content in zip(ids, responses):
        if isinstance(content, BaseModel):
            # Successful response: turn the pydantic model into a raw dict.
            record: Dict[str, Any] = content.dict()
        else:
            # Failure mode (e.g., malformed JSON).  Preserve the error string
            # so downstream analysts can inspect / retry these cases.
            record = {
                "error": str(content),
            }
        record["id"] = msg_id
        merged.append(record)
    return merged
#%%
# ---------------------------------------------------------------------------
# Main script (argument parsing & execution)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse


    os.environ["TOKENIZERS_PARALLELISM"] = "false"  # silence HF fork warning

    parser = argparse.ArgumentParser(description="Generic LLM information extraction")
    parser.add_argument("--task_id", type=str, default="country_identification", help="Task name as defined in prompts.schemas.PROMPT_REGISTRY")
    parser.add_argument("--data_dir", type=str, default="/ephemeral/home/xiong/data/Fund/Factiva_News", help="Directory containing input article JSON files")
    parser.add_argument("--output_dir", type=str, default="/ephemeral/home/xiong/data/Fund/Factiva_News/results", help="Directory to write output JSON files")
    parser.add_argument("--run_tests", action="store_true", help="Process only first JSON and first 20 articles")
    parser.add_argument("--batch_size", type=int, default=1280, help="Number of messages per LLM batch call")
    parser.add_argument("--max_tokens", type=int, default=4000, help="max_tokens argument passed to LLM completions")
    parser.add_argument("--model_args", type=str, default="./llm_args/netmind_qwen3_8b.json", help="Path to JSON file with model arguments")
    parser.add_argument("--api_key", type=str, default=None, help="API key for LLM service (overrides model_args if provided)")

    args = parser.parse_args()

    if args.task_id not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown task '{args.task_id}'. Available: {list(PROMPT_REGISTRY.keys())}")

    prompt_file = PROMPT_REGISTRY[args.task_id]["prompt_file"]  # markdown template filename
    response_model = PROMPT_REGISTRY[args.task_id]["response_model"]  # pydantic schema enforcing the response structure

    # Resolve prompt path and load template
    prompt_path = PROMPTS_DIR / prompt_file
    prompt_template = load_prompt(str(prompt_path)).sections

    # Ensure output directory exists
    output_dir = Path(args.output_dir) / args.task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Instantiate LLM agent (here pointing at a local sglang-backed Qwen server).
    # You can change `local_model_args` or parameterise them via CLI flags if
    # you wish to query a different endpoint or model.
    
    local_model_args = read_json(args.model_args)
    if not local_model_args or not isinstance(local_model_args, dict):
        raise ValueError(f"Failed to load model arguments from {args.model_args}. Check if the file exists and contains valid JSON.")
    if args.api_key:
        local_model_args["api_key"] = args.api_key
        
    batch_agent = BatchAsyncLLMAgent(**local_model_args)
    asyncio.run(batch_agent.test_connection())

    start_time = time.time()

    #json_files = sorted(glob.glob(os.path.join(args.data_dir, "*.json")))
    data_dir = Path(args.data_dir)
    json_files = list(data_dir.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files in {args.data_dir}")
    json_files = filter_unprocessed_files(json_files, output_dir, args.task_id, verbose=True)
    
    
    if args.run_tests:
        json_files = json_files[:10]
#%%
    for json_file in tqdm(json_files, desc="Processing JSON files", unit="file"):
        print(f"Processing file: {json_file}")
        articles: List[Dict[str, Any]] = read_json(json_file)
        if args.run_tests:
            articles = articles[:20]
        if not articles:
            print(f"No articles found in {json_file}, skipping.")
            continue

        batch_messages, batch_ids = _build_batch_messages_from_articles(articles, prompt_template)
        responses = asyncio.run(
            _process_articles_async(
                batch_agent,
                batch_messages,
                response_model=response_model,
                batch_size=args.batch_size,
                max_tokens=args.max_tokens,
                safe_mode=True,
            )
        )

        assert len(batch_ids) == len(responses)
        merged_results = _merge_ids_with_responses(batch_ids, responses)

        # Persist results using <input>_<task>.json naming convention so
        # multiple tasks can be run on the same article corpus without file
        # collisions.
        base_filename = os.path.splitext(os.path.basename(json_file))[0]
        output_file = os.path.join(output_dir, f"{base_filename}_{args.task_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {output_file}")

    print("All files processed.")
    print("Total time taken: ", time.time() - start_time) 
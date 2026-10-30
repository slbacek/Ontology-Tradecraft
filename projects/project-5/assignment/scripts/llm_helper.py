
# --- llm_helper.py: one shared LLM call for Steps 2, 3 and 6 ---
# Reads the API key and model from .env, sends a prompt to the LLM through
# the Perplexity API, and returns the JSON answer as a Python dictionary.
# Every answer is saved in data/llm_cache.json, so a rerun is free and
# gives the same result.

import json, os, hashlib
from pathlib import Path
from dotenv import load_dotenv
from perplexity import Perplexity

BASE = Path(__file__).resolve().parent.parent      # the assignment folder
CACHE_PATH = BASE / "data" / "llm_cache.json"

# 1) Settings from .env
load_dotenv(BASE / ".env")
MODEL = os.getenv("LLM_MODEL", "anthropic/claude-haiku-5-5")
API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not API_KEY:
    raise SystemExit("Missing PERPLEXITY_API_KEY. Copy .env.example to .env and add your key.")

# max_retries=5: wait and retry automatically if we hit the rate limit
client = Perplexity(api_key=API_KEY, max_retries=5)

# 2) Load the cache (answers from earlier runs)
if CACHE_PATH.exists():
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
else:
    cache = {}


# 3) The one function the other scripts use
def ask_llm(instructions, prompt, schema, max_tokens=500):
    """Send one prompt and return the JSON answer as a dictionary."""
    key_text = MODEL + instructions + prompt + json.dumps(schema)
    key = hashlib.sha256(key_text.encode("utf-8")).hexdigest()

    if key in cache:                       # already asked: reuse the answer
        return cache[key]

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=prompt,
        max_output_tokens=max_tokens,      # required for Anthropic models
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": schema},
        },
    )

    text = response.output_text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
    answer = json.loads(text)

    cache[key] = answer                    # save right away
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return answer
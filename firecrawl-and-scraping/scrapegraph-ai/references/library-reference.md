# ScrapeGraphAI library reference (v2.2.2)

Source of truth: the upstream repo https://github.com/ScrapeGraphAI/Scrapegraph-ai — especially `examples/` (per-graph × per-provider runnable scripts) and `examples/extras/` (one file per advanced knob).

## Graph catalog (pick by job)

| Graph | Job |
|---|---|
| `SmartScraperGraph` | One page/file + prompt (+schema) → JSON. The workhorse. |
| `SmartScraperMultiGraph` / `...MultiConcatGraph` / `...MultiBatchGraph` | Same over a list of URLs (parallel; concat = merge answers without extra LLM merge call). |
| `SmartScraperLiteGraph` / `...MultiLiteGraph` | Fetch+parse only, no LLM answer stage (cheap pre-pass). |
| `SearchGraph` | Web search → top-N results → scrape each → merged answer. `config.max_results`, `config.search_engine` (default duckduckgo; bing / searxng / serper w/ `serper_api_key`). |
| `SearchLinkGraph` / `OmniSearchGraph` | Link discovery / search + image-capable variant. |
| `OmniScraperGraph` | Page + images (vision model needed, `max_images`). |
| `DepthSearchGraph` | Crawl to depth k from a seed URL then answer. |
| `DocumentScraperGraph`, `CSVScraperGraph`, `JSONScraperGraph`, `XMLScraperGraph` (+Multi each) | Local structured files → JSON. PDF works via `source=<path>` too. |
| `MarkdownifyGraph` | Page → markdown (crawl4ai does this cheaper — prefer crawl4ai). |
| `ScriptCreatorGraph` (+Multi) | Generates a standalone Python scraper script (`library: "beautifulsoup4"` in config). |
| `ScreenshotScraperGraph` | Screenshot + OCR path (needs `ocr` extra: surya-ocr). |
| `SpeechGraph` | Answer → TTS audio file. |
| `CodeGeneratorGraph` | Prompt+schema → reusable extraction function code. |

## Config dict contract

```python
config = {
  "llm": {
    "model": "provider/model",     # e.g. "openai/gpt-4o-mini", "ollama/llama3.2",
                                   # "anthropic/claude-...", "groq/...", "google_genai/..."
    "api_key": "...",              # or provider env var (OPENAI_API_KEY, ANTHROPIC_API_KEY...)
    "temperature": 0,
    "model_tokens": 8192,          # ALWAYS set (silent 8192 fallback otherwise)
    "format": "json",              # Ollama only: forces JSON mode
    "rate_limit": {"requests_per_second": 1, "max_retries": 5},
    # "model_instance": <LangChain BaseChatModel>,  # escape hatch; then model_tokens REQUIRED
  },
  "verbose": False,
  "headless": True,
  "timeout": 480,                  # graph-level seconds
  "cache_path": False,             # path to cache fetched docs
  "loader_kwargs": {},             # → ChromiumLoader; e.g. {"slow_mo": 500,
                                   #   "backend": "undetected_chromedriver", "browser_name": "firefox"}
  "storage_state": None,           # Playwright storage_state path → authed scraping
  "html_mode": False,              # True = skip ParseNode, feed raw HTML to the LLM
  "reasoning": False,              # extra reasoning node before answer
  "reattempt": False,              # conditional regen if answer empty/"NA"
  "force": False, "cut": True,     # fetch cleanup knobs
  "additional_info": "...",        # extra instructions prepended in answer prompt
  # AVOID: "browser_base", "scrape_do" (commercial fetchers), proxy w/ free-proxy broker
}
```

Providers wired through LangChain `init_chat_model`: openai, azure_openai, google_genai, google_vertexai, ollama, groq, **anthropic (needs `pip install langchain-anthropic`)**, bedrock, mistralai, hugging_face, fireworks, togetherai (needs `langchain-together`); custom wrappers: deepseek, xai, clod, oneapi, nvidia, minimax, ernie. Context windows table: `scrapegraphai/helpers/models_tokens.py`.

## Useful patterns

- **Local source:** `source` can be a local file path or an HTML string dir — `input_key` switches to `local_dir` when source doesn't start with `http`. This is the crawl4ai-fetch + SGAI-extract hybrid.
- **Cost/exec introspection:** `graph.get_execution_info()` → per-node tokens + `total_cost_USD` (API models).
- **Multi-URL:** pass `source=[url1, url2...]` to Multi graphs; parallelism via GraphIteratorNode (batch ~16).
- **Custom pipeline:** compose nodes yourself — see `examples/custom_graph/`.
- **Async:** `await graph.run_safe_async()` (runs in executor; safe inside a running loop).
- **Burr tracing:** `config["burr_kwargs"] = {"project_name": ...}` (optional extra; local trace UI).

## Search engines (SearchGraph / utils/research_web.py)
`duckduckgo` (default, `ddgs` package, no key) · `bing` (scrape) · `searxng` (self-hosted URL) · `serper` (API key). Google-scrape variant removed in 2.x.

## Testing conventions upstream
Pytest, mock-heavy (`tests/graphs/*_test.py`); their CI runs on `pre/beta`. If we upstream a fix: branch from `origin/pre/beta`, PR base `pre/beta`, semantic commit messages (see repo `AGENTS.md`).

---
name: scrapegraph-ai
description: LLM-powered structured web extraction with the ScrapeGraphAI open-source Python library (SmartScraperGraph and friends) - prompt + optional Pydantic schema in, validated JSON out, from a URL, local HTML, PDF, or search results. Use when asked to extract structured data/JSON from a website with an LLM, scrape with a schema, scrape the top-N search results, generate a scraper script, or when ScrapeGraphAI/SmartScraperGraph is mentioned. NOT the default fetcher - crawl4ai stays the default for plain scrape/crawl/markdown; cloakbrowser for hard anti-bot targets. MANDATORY telemetry kill before first use (the env var opt-out is broken upstream).
---

# ScrapeGraphAI (open-source library)

Upstream: https://github.com/ScrapeGraphAI/Scrapegraph-ai (v2.2.2, MIT).
Full config contract + graph catalog: [references/library-reference.md](references/library-reference.md).

## Routing (do this first)

| Task | Tool |
|---|---|
| Plain page→markdown, crawl a site, batch fetch | **crawl4ai** (default, $0) |
| Hard anti-bot (DataDome, Cloudflare) | **cloakbrowser** |
| Logged-in session automation | **opencli** |
| Prompt+schema → validated JSON; search-top-N scraping; scraper-script generation | **this skill** |

Best hybrid: let crawl4ai fetch, feed saved HTML to the graph as a local source — LLM extraction without a second fetch.

## 🚨 MANDATORY before ANY run: kill telemetry

By default the library POSTs the **full parsed page content, your prompt, schema, LLM answer and URL** to `sgai-oss-tracing.onrender.com` on every successful schema scrape. `SCRAPEGRAPHAI_TELEMETRY_ENABLED=false` alone does NOT work (upstream bug: the env branch re-reads the config file). Do BOTH:

1. Ensure `~/.scrapegraphai.conf` contains:
   ```ini
   [DEFAULT]
   telemetry_enabled = false
   ```
2. In every entry script, before building any graph:
   ```python
   from scrapegraphai.telemetry import disable_telemetry
   disable_telemetry()
   ```

Never scrape personal-data (PII) pages until this is in place.

## Minimal recipe (Ollama local = $0, no egress)

```python
from scrapegraphai.telemetry import disable_telemetry
disable_telemetry()
from pydantic import BaseModel, Field
from scrapegraphai.graphs import SmartScraperGraph

class Company(BaseModel):
    name: str = Field(description="Company name")
    services: list[str] = Field(description="Services offered")

graph = SmartScraperGraph(
    prompt="Extract the company name and services offered",
    source="https://example.com",          # or a local file path / raw HTML dir
    schema=Company,
    config={
        "llm": {"model": "ollama/llama3.2", "temperature": 0,
                "model_tokens": 8192, "format": "json"},
        "headless": True,
    },
)
result = graph.run()   # dict matching Company
assert graph.model_tokens_defaulted is False
```

Install (needs Python ≥3.12, isolated venv): `pip install scrapegraphai==2.2.2 && playwright install`. **Pin the version** — the telemetry-kill sequence above was audited against 2.2.2; re-audit `scrapegraphai/telemetry/telemetry.py` before any upgrade.

## Landmines

- **`llm.model = "scrapegraphai/smart-scraper"` silently routes the job to their PAID cloud API.** Never use that model string; keep `SGAI_API_KEY` out of env.
- **Always pass `model_tokens`.** Unknown model name → silent 8192 fallback → truncated pages → wrong answers with no error. Assert `graph.model_tokens_defaulted is False` in batch code.
- **`anthropic/...` models need `pip install langchain-anthropic`** (not a base dep) and bill the paid API key — doctrine: Ollama for autonomous runs; paid Anthropic only deliberately.
- **Never enable proxy config** unless pointed at OUR proxy — the bundled `free-proxy` uses scraped public proxy lists. Never combine proxies with `storage_state` cookies.
- LLM extraction is nondeterministic: schema-validate (Pydantic) and treat an empty-but-valid dict as suspect, not as "no data" (redundancy-hides-failure doctrine).
- Windows: headless only in services (headed flashes windows); inside async code use `await graph.run_safe_async()`. Any worker fed HTML over a PIPE must `sys.stdin.reconfigure(encoding="utf-8", errors="replace")` (and stdout) first — the cp1252 default crashes on accented (French) pages.
- robots.txt is NOT checked by default pipelines — our responsibility per target.

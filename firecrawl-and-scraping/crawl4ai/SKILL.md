---
name: crawl4ai
description: >-
  Free, local web crawling and scraping engine (crawl4ai + Playwright, runs on
  this machine at ZERO per-page cost). Use this as the DEFAULT for ANY web
  scraping, crawling, or content extraction task, INSTEAD of Firecrawl (paid
  API) or WebFetch (burns a model call per page) whenever possible. Auto-trigger
  whenever the user wants to: scrape a page or site, crawl multiple/all pages of
  a site, turn a webpage into clean markdown for an LLM/RAG, extract structured
  data (products, listings, prices, tables, contacts, articles) from HTML,
  harvest links/emails/phones, grab content behind JavaScript, or batch-fetch
  many URLs cheaply. Trigger phrases: scrape, crawl, extract from URL, get the
  content of, turn this page into markdown, pull all products/listings, harvest
  emails, download a whole site, feed a page to an LLM, RAG ingestion, web data
  pipeline. Prefer this over paid crawlers for cost efficiency.
---

# crawl4ai — cheap local web crawling

crawl4ai runs a real Chromium browser locally and converts pages to clean,
LLM-ready markdown or structured JSON. **It costs nothing per page** (no API
key, no metered service). Your job is to crawl the *cheapest way that works*,
escalating only when a step genuinely needs it.

## The cost ladder — always start at the top

Pick the cheapest rung that gets the data. Never jump to an LLM when a selector
or a regex would do.

| Rung | Tool | LLM cost | Use when |
|------|------|----------|----------|
| 0 | **`WebFetch`** (built-in) | 1 small model call | You need a one-off *answer/summary* from ONE page, not the data itself |
| 1 | **`scrape.py`** → markdown | **$0** | You need the page's text/content (for reading, RAG, or feeding downstream) |
| 2 | **`extract.py`** regex mode | **$0** | You need emails, phones, prices, URLs, dates — common patterns |
| 3 | **`extract.py`** css/xpath schema | **$0** | Repeatable structured data (products, rows, listings) with stable HTML |
| 4 | **`gen_schema.py`** (once) → then rung 3 | **1 call, then $0 forever** | You need a schema but don't want to hand-write selectors |
| 5 | **`extract.py`** llm mode | per-page LLM | HTML is messy/inconsistent and no stable selector exists |

**Doctrine:** rungs 1-4 are free and should cover ~90% of real work. An LLM
(rung 5) reads the *whole page* every time you run it — that is the expensive
path. Generate a schema ONCE (rung 4) and reuse it across thousands of pages at
$0. See `references/cost-model.md` for the full decision tree and token math.

## When NOT to use crawl4ai (route elsewhere)

- **Hard bot-walls** (Cloudflare Turnstile, reCAPTCHA, FingerprintJS): use the
  `cloakbrowser` skill instead — it's the stealth-hardened browser. crawl4ai has
  a `--stealth` flag (rung below cloakbrowser) worth trying first.
- **You only want a natural-language answer about one page**, not its data:
  plain `WebFetch` is simpler.
- **Firecrawl skills**: only when crawl4ai fails on a site AND the user is fine
  paying. crawl4ai is the free-first default; Firecrawl is the paid fallback.

## Health check (run once per environment)

If a script errors with an import or browser error, verify the install:

```bash
python -c "import crawl4ai; print(crawl4ai.__version__)"   # expect 0.9.x
crawl4ai-doctor                                             # checks browser
```

If the browser is missing: `python -m playwright install chromium`.

## Quick commands

All scripts live in `scripts/` beside this file and are self-contained CLIs.
Resolve `<skill>` to this skill's directory. Every script prints JSON or writes
a file; none needs an API key except `llm` mode.

```bash
# Rung 1 — page → clean markdown (fit_markdown, noise stripped)
python <skill>/scripts/scrape.py "https://example.com" -o page.md

# Rung 1 — raw markdown (no filtering), plus links + media as JSON
python <skill>/scripts/scrape.py "https://example.com" --raw --json -o page.json

# Rung 2 — harvest emails/phones/urls/prices (zero LLM)
python <skill>/scripts/extract.py "https://example.com" --regex email,phone_us,url

# Rung 3 — structured extraction with a CSS schema (zero LLM)
python <skill>/scripts/extract.py "https://site.com/products" --schema schema.json

# Rung 4 — generate a reusable schema ONCE from a sample page
python <skill>/scripts/gen_schema.py "https://site.com/products" \
    --query "product name, price, rating, product url" -o schema.json

# Rung 5 — LLM extraction (only when no stable selector exists)
python <skill>/scripts/extract.py "https://site.com" --llm \
    --instruction "extract each job's title, company, location, salary"

# Crawl a whole section of a site (BFS, depth-limited, filtered)
python <skill>/scripts/deep_crawl.py "https://docs.site.com" \
    --max-depth 2 --max-pages 40 --include "*guide*,*tutorial*" -o out_dir/

# Batch many URLs concurrently with rate limiting (memory-adaptive)
python <skill>/scripts/batch.py urls.txt -o out_dir/ --concurrency 8
```

Run any script with `-h` for its full option list.

## Core efficiency habits

1. **Caching is on by default.** Repeated crawls of the same URL are instant and
   free. Pass `--fresh` only when you need live content. This alone kills most
   redundant work.
2. **Prefer `fit_markdown` over raw** when feeding an LLM downstream — the
   pruning filter drops nav/footer/boilerplate, cutting downstream tokens 40-70%.
3. **Extract, don't summarize.** If the user wants *data*, use a schema (rung 3),
   not an LLM reading prose. Selectors are deterministic and free.
4. **Batch with `arun_many`**, never a Python loop of single crawls — one browser,
   shared pool, memory-adaptive concurrency. See `references/scale-and-stealth.md`.
5. **Amortize the one LLM cost.** When HTML is irregular, spend ONE call on
   `gen_schema.py`, save the JSON, then run rung 3 forever. Never re-run rung 5
   on pages that share a template.

## Deeper references (load only when the task needs them)

- `references/cost-model.md` — full decision tree, token math, tool routing.
- `references/extraction.md` — complete CSS/XPath schema spec, field types,
  nested/list/sibling selectors, regex patterns, schema-gen tips.
- `references/markdown-filtering.md` — PruningContentFilter vs BM25, fit vs raw,
  RAG chunking, screenshots/PDF.
- `references/deep-crawl.md` — BFS/DFS/BestFirst strategies, filter chains,
  keyword scorers, streaming.
- `references/scale-and-stealth.md` — arun_many, dispatchers, rate limiting,
  proxies, sessions, persistent login profiles, JS execution, magic/stealth mode.

# Cost model & tool routing — how to crawl cheap

The single biggest cost lever in web crawling is **not calling an LLM when you
don't have to.** crawl4ai runs a real browser locally, so fetching + rendering +
markdown + selector/regex extraction are all effectively free (compute only).
The only metered step is if you deliberately invoke an LLM to read a page.

## The decision tree

```
What does the user actually need?
│
├─ A natural-language ANSWER about one page ("what does this say about X?")
│     -> WebFetch (built-in). One small model call. Don't spin up a browser.
│
├─ The page's CONTENT (to read, store, or feed downstream / RAG)
│     -> scrape.py            [rung 1, $0]   fit_markdown by default
│
├─ Common PATTERNS (emails, phones, prices, urls, dates, ids)
│     -> extract.py --regex   [rung 2, $0]
│
├─ Repeatable STRUCTURED rows and the HTML is consistent
│     ├─ you can name selectors  -> extract.py --schema   [rung 3, $0]
│     └─ you can't/won't          -> gen_schema.py --sample (agent writes it, $0)
│                                     then extract.py --schema   [rung 3, $0]
│
├─ Structured data but HTML is MESSY / varies page to page
│     -> gen_schema.py --llm ONCE, save JSON, then rung 3 forever
│        (one metered call amortized over every future page)
│
├─ Truly irregular, one-off, semantic ("summarise sentiment per review")
│     -> extract.py --llm      [rung 5, metered PER PAGE] — last resort
│
├─ MANY urls
│     -> batch.py (arun_many, one browser pool, rate-limited)   [$0]
│
└─ A whole SITE / section
      -> deep_crawl.py (BFS/DFS/best-first, filtered, capped)   [$0]
```

## Why the rungs matter (token math)

An LLM extraction (rung 5) sends the page's text to a model **every single run**.
A 3,000-word product page is ~4,000 input tokens; extract from 1,000 such pages
and you've burned ~4M tokens *and pay it again* every time you re-run.

A CSS schema (rung 3) sends **zero** tokens. You pay once — either $0 (agent
hand-writes the schema from a sample) or one ~4k-token call (`gen_schema --llm`)
— and every subsequent page across the whole site is free and deterministic.

**Rule of thumb: if pages share a template, you should touch an LLM at most
once for that template, ever.** Re-running rung 5 on templated pages is the
single most common way to waste money on crawling. Don't.

## fit_markdown saves downstream tokens too

Even when the *next* step is an LLM you don't control (e.g. feeding content to a
RAG pipeline or a summariser), prefer `fit_markdown` (the default in scrape.py)
over raw. The PruningContentFilter strips nav bars, cookie banners, footers,
and sidebars — typically **40-70% fewer tokens** for the same signal. Pass
`--raw` only when you genuinely need the boilerplate.

## Caching = free re-runs

crawl4ai caches by URL (SQLite, on disk). By default the skill's scripts read
cache (`CacheMode.ENABLED`), so re-scraping a URL you already fetched is instant
and costs nothing. Only pass `--fresh` when you need live/changed content. When
iterating on a schema, this means you fetch the page once and test selectors
against the cache repeatedly for free.

## Routing vs the other installed skills

| Situation | Use | Why |
|-----------|-----|-----|
| Any normal scrape/crawl/extract | **crawl4ai** (this skill) | free, local, no API |
| Hard bot-wall (Cloudflare Turnstile, reCAPTCHA, fingerprinting) | **cloakbrowser** | purpose-built stealth; try `crawl4ai --stealth` first |
| One-off NL answer about a single page | **WebFetch** | no browser needed, one tiny call |
| crawl4ai failed on a site AND paying is OK | **firecrawl-*** | managed paid fallback, handles some sites crawl4ai can't |
| Google/Bing style web search for URLs | **smart-search** / WebSearch | discovery, not extraction |

Default order: **crawl4ai → (stealth) → cloakbrowser → firecrawl (paid).**
Start free, escalate only on failure.

## Quick cost sanity checklist before a big job

1. Do these pages share a template? → generate ONE schema, rung 3 for the rest.
2. Am I about to loop rung 5 over many pages? → stop, write a schema instead.
3. Is the downstream consumer an LLM? → use fit_markdown, not raw.
4. Re-running something I already fetched? → drop `--fresh`, hit the cache.
5. Many URLs? → batch.py, not a shell loop (shares the browser, rate-limits).

# Markdown generation & content filtering

Goal: produce the *smallest clean markdown that keeps the signal*, so downstream
LLM tokens (and your storage) stay low. `scripts/scrape.py` handles this.

## raw vs fit markdown

Every crawl produces a markdown object with two views:

- `result.markdown.raw_markdown` — faithful HTML→markdown of the whole page
  (includes nav, footer, cookie bars, sidebars).
- `result.markdown.fit_markdown` — after a content filter prunes low-signal
  blocks. **This is the default in scrape.py** and what you want for RAG/LLM
  input. Typically 40-70% smaller than raw for the same meaning.

Get raw with `scrape.py URL --raw`. Get fit (default) with just `scrape.py URL`.

## Content filters

### PruningContentFilter (default, no query needed)
Scores DOM blocks by text density, link density, and position, and drops the
low scorers (nav, boilerplate). Good general-purpose cleaner.

```python
from crawl4ai.content_filter_strategy import PruningContentFilter
PruningContentFilter(threshold=0.48, threshold_type="dynamic")
# threshold_type="fixed" -> hard cutoff at threshold
# threshold_type="dynamic" -> adapts per page (what scrape.py uses)
# higher threshold = more aggressive pruning
```

### BM25ContentFilter (query-focused)
When you only want blocks relevant to a topic/question, BM25-rank blocks against
a query and keep the top ones. Ideal for "get me just the pricing section".

```python
from crawl4ai.content_filter_strategy import BM25ContentFilter
BM25ContentFilter(user_query="pricing and plans", bm25_threshold=1.0)
```

scrape.py uses PruningContentFilter. For a query-focused pull, either use
`--css` to target the region, or edit the generator in scrape.py to BM25 for a
one-off (it's ~2 lines). For repeated topic extraction prefer a CSS schema.

## Feeding an LLM / RAG downstream

- Always prefer **fit_markdown** as LLM input — you pay for tokens you send.
- Use `--css "article"` (or `main`, `.content`) to hard-scope to the body when
  you know the container — cheaper and cleaner than any filter.
- crawl4ai can also emit citation-style links and a references section; the raw
  markdown preserves link text. For pure semantic content, fit is enough.
- Chunk *after* fitting, not before — you don't want to embed nav bars.

## Screenshots & PDF

For visual capture (not for text extraction — that's wasteful):

```
scrape.py URL --screenshot shot.png     # full-page PNG
scrape.py URL --pdf page.pdf            # PDF render
```

Use these only when the user wants an image/PDF artifact. To read a page's
*content*, never screenshot-then-OCR — go straight to markdown (cheaper, exact).

## JSON output (content + links + media in one pass)

`scrape.py URL --json` returns markdown plus `internal_links`, `external_links`,
and `images` — handy for building a crawl frontier or a link map without a
second fetch.

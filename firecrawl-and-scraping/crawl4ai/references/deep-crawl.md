# Deep crawling reference (whole-site, multi-page)

Crawl many linked pages of one site to markdown files. Zero LLM cost. Driver:
`scripts/deep_crawl.py`. Always cap with `--max-pages` so a crawl can't run away.

## Strategies

| `--strategy` | class | behaviour | pick when |
|--------------|-------|-----------|-----------|
| `bfs` (default) | BFSDeepCrawlStrategy | all links at depth N before N+1 | full, even coverage of a section |
| `dfs` | DFSDeepCrawlStrategy | dive down one branch first | reach deep leaf pages fast |
| `best` | BestFirstCrawlingStrategy | visit highest-scoring URLs first | you care about *relevance*, not coverage; needs `--keywords` |

Shared knobs: `--max-depth` (levels beyond the start page), `--max-pages` (hard
total cap), `--external` (follow off-domain links; default off).

## Filtering the frontier (spend crawls only where they matter)

`deep_crawl.py` builds a FilterChain from your flags:

- `--include "*guide*,*docs*"` → URLPatternFilter (glob match on the URL).
- `--allowed-domains "docs.site.com"` → DomainFilter.
- ContentTypeFilter for `text/html` is always applied (skips PDFs/images).

Filtering *before* fetching is the whole game: a tight `--include` on a big site
turns a 10,000-page crawl into the 40 pages you actually want.

## Relevance scoring (best-first)

```
deep_crawl.py URL --strategy best --keywords "pricing,plans,enterprise" --max-pages 25
```

KeywordRelevanceScorer scores each discovered URL by keyword match; best-first
visits the top scorers first. Combined with `--max-pages`, you get the 25 most
relevant pages instead of the first 25 found. `score_threshold` (in the strategy)
can also drop low-scoring URLs entirely.

## Output

One `<slug>.md` per page (fit_markdown, pruned) plus `index.json` mapping every
`url → file, depth, score`. Streaming is on, so pages are written as they finish
— a crash mid-crawl still leaves you everything crawled so far.

## Recipes

```bash
# Every doc/guide page, 2 deep, capped
deep_crawl.py "https://docs.site.com" --max-depth 2 --max-pages 60 --include "*docs*,*guide*" -o docs/

# Just the blog, newest-relevance first
deep_crawl.py "https://site.com/blog" --strategy best --keywords "launch,release,changelog" --max-pages 30 -o blog/

# A product catalog section, stay on domain, then extract each with a schema:
deep_crawl.py "https://shop.com/category/shoes" --max-pages 100 --include "*/product/*" -o shoe_pages/
#   ... then run extract.py --schema over the saved pages, or use batch.py with --schema on index.json URLs.
```

## Cost note

Deep crawl produces markdown for free. If you then need *structured* data from
every crawled page, don't LLM each one — pull the URLs from `index.json` and run
`batch.py <urls> --schema your_schema.json` (rung 3, still $0). One schema, whole
site.

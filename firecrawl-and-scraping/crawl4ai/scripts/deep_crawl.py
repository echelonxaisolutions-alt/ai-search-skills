#!/usr/bin/env python
"""deep_crawl.py — crawl many pages of ONE site, depth-limited and filtered.

Zero LLM cost. Writes one .md per page to an output dir (+ an index.json). Use
this for "crawl the whole docs section", "get every product page under /shop",
"download this blog". Always set --max-pages so it can't run away.

Strategies:
  bfs       breadth-first (default): level-by-level, good for full coverage
  dfs       depth-first: dive down one branch first
  best      best-first: visit highest-scoring URLs first (needs --keywords)

Examples:
  # All guide/tutorial pages, 2 levels deep, capped at 40 pages
  python deep_crawl.py "https://docs.site.com" \
      --max-depth 2 --max-pages 40 --include "*guide*,*tutorial*" -o out/

  # Prioritise pages about pricing/plans, stay on domain
  python deep_crawl.py "https://site.com" --strategy best \
      --keywords "pricing,plans,cost" --max-pages 25 -o out/
"""
import argparse
import json
import os
import re
import sys

from _common import run, browser_config, cache_mode, eprint


def slugify(url):
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")
    return (s or "index")[:120] + ".md"


async def deep(args):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.deep_crawling import (
        BFSDeepCrawlStrategy, DFSDeepCrawlStrategy, BestFirstCrawlingStrategy)
    from crawl4ai.deep_crawling.filters import (
        FilterChain, URLPatternFilter, DomainFilter, ContentTypeFilter)
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter

    filters = [ContentTypeFilter(allowed_types=["text/html"])]
    if args.include:
        filters.append(URLPatternFilter(patterns=[p.strip() for p in args.include.split(",")]))
    if args.allowed_domains:
        filters.append(DomainFilter(allowed_domains=[d.strip() for d in args.allowed_domains.split(",")]))
    filter_chain = FilterChain(filters)

    scorer = None
    if args.keywords:
        from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
        scorer = KeywordRelevanceScorer(
            keywords=[k.strip() for k in args.keywords.split(",")], weight=0.7)

    common = dict(max_depth=args.max_depth, include_external=args.external,
                  max_pages=args.max_pages, filter_chain=filter_chain)
    if args.strategy == "dfs":
        strat = DFSDeepCrawlStrategy(url_scorer=scorer, **common)
    elif args.strategy == "best":
        strat = BestFirstCrawlingStrategy(url_scorer=scorer, **common)
    else:
        strat = BFSDeepCrawlStrategy(url_scorer=scorer, **common)

    md_gen = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="dynamic"))
    config = CrawlerRunConfig(
        deep_crawl_strategy=strat,
        markdown_generator=md_gen,
        cache_mode=cache_mode(args.fresh),
        stream=True,
        page_timeout=args.timeout,
        verbose=False,
    )

    os.makedirs(args.output, exist_ok=True)
    index = []
    n = 0
    async with AsyncWebCrawler(config=browser_config(stealth=args.stealth)) as crawler:
        async for result in await crawler.arun(url=args.url, config=config):
            if not result.success:
                eprint("skip", result.url, result.error_message)
                continue
            md = getattr(result.markdown, "fit_markdown", None) or \
                 getattr(result.markdown, "raw_markdown", None) or str(result.markdown)
            fname = slugify(result.url)
            with open(os.path.join(args.output, fname), "w", encoding="utf-8") as f:
                f.write(f"<!-- {result.url} -->\n\n{md}")
            meta = result.metadata or {}
            index.append({"url": result.url, "file": fname,
                          "depth": meta.get("depth"), "score": meta.get("score")})
            n += 1
            eprint(f"[{n}] depth={meta.get('depth')} {result.url}")

    with open(os.path.join(args.output, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    eprint(f"done: {n} pages -> {args.output}/  (index.json written)")


def main():
    p = argparse.ArgumentParser(description="Deep-crawl one site to markdown files (zero LLM).")
    p.add_argument("url")
    p.add_argument("-o", "--output", required=True, help="output directory")
    p.add_argument("--strategy", choices=["bfs", "dfs", "best"], default="bfs")
    p.add_argument("--max-depth", type=int, default=2, help="levels beyond the start page")
    p.add_argument("--max-pages", type=int, default=50, help="hard cap on total pages")
    p.add_argument("--include", help="URL glob patterns, comma list, e.g. '*docs*,*guide*'")
    p.add_argument("--allowed-domains", help="restrict to these domains (comma list)")
    p.add_argument("--keywords", help="relevance keywords (comma) — enables scoring")
    p.add_argument("--external", action="store_true", help="follow off-domain links too")
    p.add_argument("--stealth", action="store_true")
    p.add_argument("--fresh", action="store_true", help="bypass cache")
    p.add_argument("--timeout", type=int, default=60000)
    args = p.parse_args()
    run(deep(args))


if __name__ == "__main__":
    main()

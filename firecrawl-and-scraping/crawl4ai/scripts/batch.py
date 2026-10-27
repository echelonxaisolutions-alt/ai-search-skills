#!/usr/bin/env python
"""batch.py — crawl MANY urls concurrently, one browser pool, rate-limited.

Zero LLM cost (unless you pass --schema, still zero — CSS extraction). Use this
instead of a shell loop of scrape.py: one browser, memory-adaptive concurrency,
automatic 429/503 backoff. Writes one .md (or .json per-URL rows) per URL + a
manifest.

Input: a file with one URL per line (blank lines / # comments ignored), or pass
URLs as extra args.

Examples:
  python batch.py urls.txt -o out/ --concurrency 8
  python batch.py urls.txt -o out/ --schema products.json     # extract each
  python batch.py https://a.com https://b.com -o out/
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
    return (s or "index")[:120]


def load_urls(args):
    urls = []
    for a in args.inputs:
        if os.path.isfile(a):
            with open(a, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)
        else:
            urls.append(a)
    # de-dupe, keep order
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


async def batch(args):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, RateLimiter
    from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter

    urls = load_urls(args)
    if not urls:
        eprint("no URLs given"); sys.exit(1)

    cfg_kwargs = dict(cache_mode=cache_mode(args.fresh), stream=True,
                      page_timeout=args.timeout)
    if args.schema:
        from crawl4ai import JsonCssExtractionStrategy
        cfg_kwargs["extraction_strategy"] = JsonCssExtractionStrategy(json.load(open(args.schema)))
    else:
        cfg_kwargs["markdown_generator"] = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="dynamic"))
    config = CrawlerRunConfig(**cfg_kwargs)

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=args.mem_threshold,
        max_session_permit=args.concurrency,
        rate_limiter=RateLimiter(base_delay=(args.min_delay, args.max_delay),
                                 max_delay=30.0, max_retries=3,
                                 rate_limit_codes=[429, 503]),
    )

    os.makedirs(args.output, exist_ok=True)
    manifest, ok, fail = [], 0, 0
    async with AsyncWebCrawler(config=browser_config(stealth=args.stealth)) as crawler:
        async for result in await crawler.arun_many(urls=urls, config=config, dispatcher=dispatcher):
            base = slugify(result.url)
            if not result.success:
                fail += 1
                manifest.append({"url": result.url, "ok": False, "error": result.error_message})
                eprint("FAIL", result.url, result.error_message)
                continue
            ok += 1
            if args.schema and result.extracted_content:
                fname = base + ".json"
                open(os.path.join(args.output, fname), "w", encoding="utf-8").write(result.extracted_content)
            else:
                fname = base + ".md"
                md = getattr(result.markdown, "fit_markdown", None) or \
                     getattr(result.markdown, "raw_markdown", None) or str(result.markdown)
                open(os.path.join(args.output, fname), "w", encoding="utf-8").write(md)
            manifest.append({"url": result.url, "ok": True, "file": fname})
            eprint("ok", result.url)

    with open(os.path.join(args.output, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    eprint(f"done: {ok} ok, {fail} failed -> {args.output}/  (manifest.json)")


def main():
    p = argparse.ArgumentParser(description="Concurrent multi-URL crawl (zero LLM).")
    p.add_argument("inputs", nargs="+", help="a urls.txt file and/or literal URLs")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--schema", help="CSS schema JSON — extract rows from each URL instead of markdown")
    p.add_argument("--concurrency", type=int, default=8, help="max concurrent pages")
    p.add_argument("--mem-threshold", type=float, default=85.0, help="pause above this %% RAM")
    p.add_argument("--min-delay", type=float, default=0.5, help="min polite delay between requests")
    p.add_argument("--max-delay", type=float, default=2.0, help="max polite delay")
    p.add_argument("--stealth", action="store_true")
    p.add_argument("--fresh", action="store_true", help="bypass cache")
    p.add_argument("--timeout", type=int, default=60000)
    args = p.parse_args()
    run(batch(args))


if __name__ == "__main__":
    main()

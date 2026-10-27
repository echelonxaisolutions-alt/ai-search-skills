#!/usr/bin/env python
"""gen_schema.py — get a reusable CSS extraction schema (rung 4). Two paths.

The point of a schema is to pay for structure understanding ONCE, then extract
from thousands of same-template pages at $0 (rung 3). So generating the schema
cheaply matters.

DEFAULT PATH (free): dump a trimmed HTML sample of the repeating region. YOU
(the agent) read it and hand-write the schema JSON — no extra API bill, because
you're already in context. This is the cheapest option and usually the best.

  python gen_schema.py "https://site.com/shop" --sample
  # -> prints cleaned HTML; agent writes products.json with baseSelector+fields

LLM PATH (one metered call, then free forever): let crawl4ai infer the schema.

  python gen_schema.py "https://site.com/shop" \
      --query "product name, price, rating, url" --llm -o products.json

Either way, save the schema and feed it to:  extract.py URL --schema products.json
"""
import argparse
import json
import re
import sys

from _common import run, browser_config, cache_mode, eprint


async def gen(args):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

    if args.llm:
        # crawl4ai's built-in generator: one LLM call, validated against real HTML.
        from crawl4ai import JsonCssExtractionStrategy, LLMConfig
        if not args.query:
            eprint("--llm needs --query describing the fields to extract")
            sys.exit(1)
        schema = JsonCssExtractionStrategy.generate_schema(
            url=args.url,
            query=args.query,
            llm_config=LLMConfig(provider=args.provider, api_token=args.api_token),
            schema_type="css",
            validate=True,
        )
        out = json.dumps(schema, indent=2, ensure_ascii=False)
        if args.output:
            open(args.output, "w", encoding="utf-8").write(out)
            eprint(f"schema -> {args.output}  (now reuse with extract.py --schema)")
        else:
            print(out)
        return

    # DEFAULT: dump a cleaned HTML sample for the agent to author the schema.
    config = CrawlerRunConfig(cache_mode=cache_mode(args.fresh), page_timeout=args.timeout)
    if args.css:
        config.css_selector = args.css
    if args.wait:
        config.wait_for = args.wait
    async with AsyncWebCrawler(config=browser_config()) as crawler:
        result = await crawler.arun(url=args.url, config=config)
    if not result.success:
        eprint("FAILED:", result.error_message)
        sys.exit(2)

    html = result.cleaned_html or result.html or ""
    # Strip script/style/svg noise so the agent sees structure, not payload.
    html = re.sub(r"<(script|style|svg|noscript)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
    html = re.sub(r"\s+", " ", html)
    sample = html[: args.chars]
    print("<!-- HTML SAMPLE (author a schema: pick baseSelector = the repeating"
          " container, then one field per datum). Full spec: references/extraction.md -->")
    print(sample)
    if len(html) > args.chars:
        eprint(f"(truncated to {args.chars} of {len(html)} chars; raise --chars if needed)")


def main():
    p = argparse.ArgumentParser(description="Generate/aid a reusable CSS extraction schema.")
    p.add_argument("url")
    p.add_argument("-o", "--output")
    p.add_argument("--sample", action="store_true", help="(default) dump HTML sample for hand-authoring")
    p.add_argument("--css", help="limit the sample to this region (e.g. 'main', '.product-grid')")
    p.add_argument("--chars", type=int, default=8000, help="HTML sample size")
    p.add_argument("--llm", action="store_true", help="use crawl4ai's LLM schema generator (one call)")
    p.add_argument("--query", help="fields to extract, for --llm")
    p.add_argument("--provider", default="openai/gpt-4o-mini")
    p.add_argument("--api-token")
    p.add_argument("--wait")
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--timeout", type=int, default=60000)
    args = p.parse_args()
    run(gen(args))


if __name__ == "__main__":
    main()

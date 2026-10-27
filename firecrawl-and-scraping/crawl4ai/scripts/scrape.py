#!/usr/bin/env python
"""scrape.py — one page -> clean markdown (or JSON with links/media). Zero LLM cost.

Rung 1 of the cost ladder. This is the default, cheapest way to get a page's
content. Uses fit_markdown (noise-pruned) by default so downstream LLM tokens
stay low.

Examples:
  python scrape.py "https://example.com"                 # fit markdown to stdout
  python scrape.py "https://example.com" -o page.md      # write to file
  python scrape.py "https://example.com" --raw           # no pruning filter
  python scrape.py "https://example.com" --json -o p.json# markdown+links+media
  python scrape.py "https://example.com" --css "article" # only this region
  python scrape.py "https://spa.com" --wait "css:.loaded"# wait for JS content
  python scrape.py "https://example.com" --screenshot shot.png
"""
import argparse
import json
import sys

from _common import run, browser_config, cache_mode, eprint


async def scrape(args):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter

    md_gen = None
    if not args.raw:
        # PruningContentFilter drops low-signal blocks (nav, footers, sidebars).
        # threshold 0.48 is a good general default; higher = more aggressive.
        md_gen = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="dynamic")
        )

    cfg_kwargs = dict(
        cache_mode=cache_mode(args.fresh),
        word_count_threshold=args.min_words,
        page_timeout=args.timeout,
        screenshot=bool(args.screenshot),
        pdf=bool(args.pdf),
        exclude_external_links=args.no_external_links,
        remove_overlay_elements=True,
    )
    if md_gen is not None:
        cfg_kwargs["markdown_generator"] = md_gen
    if args.css:
        cfg_kwargs["css_selector"] = args.css
    if args.wait:
        cfg_kwargs["wait_for"] = args.wait
    if args.js:
        cfg_kwargs["js_code"] = [args.js]
    if args.magic:
        cfg_kwargs["magic"] = True

    config = CrawlerRunConfig(**cfg_kwargs)
    bcfg = browser_config(stealth=args.stealth, headless=not args.headed,
                          proxy=args.proxy, user_data_dir=args.profile)

    async with AsyncWebCrawler(config=bcfg) as crawler:
        result = await crawler.arun(url=args.url, config=config)

    if not result.success:
        eprint("FAILED:", result.error_message)
        sys.exit(2)

    md_obj = result.markdown
    fit = getattr(md_obj, "fit_markdown", None)
    raw = getattr(md_obj, "raw_markdown", None) or str(md_obj)
    markdown = raw if args.raw else (fit or raw)

    if args.screenshot and result.screenshot:
        import base64
        with open(args.screenshot, "wb") as f:
            f.write(base64.b64decode(result.screenshot))
        eprint("screenshot ->", args.screenshot)
    if args.pdf and result.pdf:
        with open(args.pdf, "wb") as f:
            f.write(result.pdf)
        eprint("pdf ->", args.pdf)

    if args.json:
        payload = {
            "url": result.url,
            "success": result.success,
            "markdown": markdown,
            "title": (result.metadata or {}).get("title"),
            "internal_links": [l.get("href") for l in (result.links or {}).get("internal", [])],
            "external_links": [l.get("href") for l in (result.links or {}).get("external", [])],
            "images": [m.get("src") for m in (result.media or {}).get("images", [])],
        }
        out = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        out = markdown

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        eprint(f"wrote {len(out)} chars -> {args.output}")
    else:
        print(out)


def main():
    p = argparse.ArgumentParser(description="Scrape one page to markdown/JSON (zero LLM cost).")
    p.add_argument("url")
    p.add_argument("-o", "--output", help="write to file instead of stdout")
    p.add_argument("--json", action="store_true", help="emit JSON (markdown+links+images)")
    p.add_argument("--raw", action="store_true", help="raw markdown, skip the pruning filter")
    p.add_argument("--css", help="CSS selector to limit scraping to a region")
    p.add_argument("--wait", help="wait_for condition, e.g. 'css:.results' or 'js:() => window.ready'")
    p.add_argument("--js", help="JS snippet to run before scraping (e.g. click/scroll)")
    p.add_argument("--magic", action="store_true", help="magic mode: auto-dismiss popups, simulate user")
    p.add_argument("--stealth", action="store_true", help="enable stealth browser patches")
    p.add_argument("--headed", action="store_true", help="show the browser window")
    p.add_argument("--proxy", help="proxy URL, e.g. http://user:pass@host:port")
    p.add_argument("--profile", help="persistent user_data_dir for a logged-in session")
    p.add_argument("--fresh", action="store_true", help="bypass cache, fetch live")
    p.add_argument("--no-external-links", action="store_true", help="drop off-domain links")
    p.add_argument("--min-words", type=int, default=0, help="word_count_threshold per block")
    p.add_argument("--timeout", type=int, default=60000, help="page_timeout in ms")
    p.add_argument("--screenshot", help="save a PNG screenshot to this path")
    p.add_argument("--pdf", help="save a PDF to this path")
    args = p.parse_args()
    run(scrape(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""extract.py — structured data out of a page. Three modes, cheapest first.

  --regex   rung 2: built-in patterns (email/phone/url/price...). Zero LLM.
  --schema  rung 3: CSS/XPath schema -> JSON rows. Zero LLM. The workhorse.
  --llm     rung 5: LLM reads the page. Costs per page. Last resort.

Always try --regex or --schema before --llm. If you don't have a schema yet,
generate one ONCE with gen_schema.py, save it, and reuse it forever at $0.

Examples:
  # Rung 2 — harvest common patterns
  python extract.py "https://site.com/contact" --regex email,phone_us

  # Rung 3 — CSS schema from a file
  python extract.py "https://site.com/shop" --schema products.json -o rows.json

  # Rung 3 — inline one-off schema
  python extract.py "https://news.ycombinator.com" \
      --base "tr.athing" \
      --field "title:span.titleline a:text" \
      --field "url:span.titleline a:attr:href"

  # Rung 5 — LLM (needs a provider; defaults to env keys)
  python extract.py "https://site.com" --llm \
      --instruction "each product: name, price, in_stock (bool)"
"""
import argparse
import json
import sys

from _common import run, browser_config, cache_mode, eprint


def parse_inline_fields(field_args):
    """'name:selector:type[:attr]' -> schema field dict."""
    fields = []
    for spec in field_args:
        parts = spec.split(":")
        if len(parts) < 2:
            eprint(f"bad --field '{spec}', want name:selector[:type[:attr]]")
            sys.exit(1)
        name, selector = parts[0], parts[1]
        ftype = parts[2] if len(parts) > 2 else "text"
        f = {"name": name, "selector": selector, "type": ftype}
        if ftype == "attribute" or ftype == "attr":
            f["type"] = "attribute"
            f["attribute"] = parts[3] if len(parts) > 3 else "href"
        fields.append(f)
    return fields


async def extract(args):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

    strategy = None
    if args.regex:
        from crawl4ai import RegexExtractionStrategy
        names = [n.strip() for n in args.regex.split(",") if n.strip()]
        pattern = None
        for n in names:
            attr = "".join(w.capitalize() for w in n.split("_"))  # phone_us -> PhoneUs
            # normalise a few common aliases to the library's attribute names
            alias = {"PhoneUs": "PhoneUS", "Url": "Url", "Ipv4": "IPv4",
                     "Ipv6": "IPv6", "DateUs": "DateUS", "PostalUs": "PostalUS",
                     "PostalUk": "PostalUK"}.get(attr, attr)
            bit = getattr(RegexExtractionStrategy, alias, None)
            if bit is None:
                eprint(f"unknown regex pattern '{n}'. See references/extraction.md.")
                sys.exit(1)
            pattern = bit if pattern is None else (pattern | bit)
        strategy = RegexExtractionStrategy(pattern=pattern)

    elif args.llm:
        from crawl4ai import LLMExtractionStrategy, LLMConfig
        llm_config = LLMConfig(provider=args.provider, api_token=args.api_token)
        strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            extraction_type="schema" if args.json_schema else "block",
            schema=json.load(open(args.json_schema)) if args.json_schema else None,
            instruction=args.instruction or "Extract the key structured data as JSON.",
            extra_args={"temperature": 0},
        )

    else:  # schema mode (rung 3)
        from crawl4ai import JsonCssExtractionStrategy, JsonXPathExtractionStrategy
        if args.schema:
            schema = json.load(open(args.schema))
        elif args.base and args.field:
            schema = {"name": "inline", "baseSelector": args.base,
                      "fields": parse_inline_fields(args.field)}
        else:
            eprint("schema mode needs --schema FILE or (--base SELECTOR + --field ...)")
            sys.exit(1)
        Strat = JsonXPathExtractionStrategy if args.xpath else JsonCssExtractionStrategy
        strategy = Strat(schema)

    config = CrawlerRunConfig(
        cache_mode=cache_mode(args.fresh),
        extraction_strategy=strategy,
        page_timeout=args.timeout,
    )
    if args.wait:
        config.wait_for = args.wait
    if args.js:
        config.js_code = [args.js]

    bcfg = browser_config(stealth=args.stealth, proxy=args.proxy)
    async with AsyncWebCrawler(config=bcfg) as crawler:
        result = await crawler.arun(url=args.url, config=config)

    if not result.success:
        eprint("FAILED:", result.error_message)
        sys.exit(2)
    if not result.extracted_content:
        eprint("no content extracted (check your selectors / patterns)")
        sys.exit(3)

    data = json.loads(result.extracted_content)
    out = json.dumps(data, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        n = len(data) if isinstance(data, list) else 1
        eprint(f"extracted {n} record(s) -> {args.output}")
    else:
        print(out)


def main():
    p = argparse.ArgumentParser(description="Extract structured data (regex/css/xpath/llm).")
    p.add_argument("url")
    p.add_argument("-o", "--output")
    # mode selectors
    p.add_argument("--regex", help="comma list: email,phone_us,url,currency,date_iso,...")
    p.add_argument("--schema", help="path to a CSS/XPath schema JSON (rung 3)")
    p.add_argument("--base", help="inline baseSelector (container repeated per row)")
    p.add_argument("--field", action="append", default=[],
                   help="inline field 'name:selector[:type[:attr]]' (repeatable)")
    p.add_argument("--xpath", action="store_true", help="treat selectors as XPath")
    p.add_argument("--llm", action="store_true", help="rung 5: LLM extraction (costs per page)")
    p.add_argument("--instruction", help="LLM extraction instruction")
    p.add_argument("--json-schema", help="pydantic-style JSON schema for --llm")
    p.add_argument("--provider", default="openai/gpt-4o-mini", help="LLM provider id")
    p.add_argument("--api-token", help="LLM api token (else uses provider env var)")
    # shared
    p.add_argument("--wait", help="wait_for condition")
    p.add_argument("--js", help="JS to run before extraction")
    p.add_argument("--stealth", action="store_true")
    p.add_argument("--proxy")
    p.add_argument("--fresh", action="store_true", help="bypass cache")
    p.add_argument("--timeout", type=int, default=60000)
    args = p.parse_args()
    run(extract(args))


if __name__ == "__main__":
    main()

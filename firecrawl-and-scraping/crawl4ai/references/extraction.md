# Structured extraction reference (zero-LLM)

Everything here runs with **no LLM call**. This is rung 2-4 of the cost ladder.
Use `scripts/extract.py`. Contents:

1. CSS/XPath schema format (the workhorse)
2. Field types (text/attribute/html/nested/list/nested_list)
3. Sibling selectors
4. Regex patterns (built-in + custom)
5. Authoring a schema from a sample (cheapest)
6. Common gotchas

---

## 1. Schema format

A schema is a dict. `baseSelector` picks the *repeating container* (one per
output row); `fields` pull data out of each container.

```python
schema = {
    "name": "Products",
    "baseSelector": "div.product-card",     # one row per match
    "baseFields": [                          # optional: read the container itself
        {"name": "product_id", "type": "attribute", "attribute": "data-id"}
    ],
    "fields": [
        {"name": "title",  "selector": "h2.name", "type": "text"},
        {"name": "price",  "selector": "span.price", "type": "text"},
        {"name": "url",    "selector": "a.link", "type": "attribute", "attribute": "href"},
        {"name": "image",  "selector": "img", "type": "attribute", "attribute": "src"},
        {"name": "summary","selector": "div.desc", "type": "html", "default": ""},
    ]
}
```

Feed it via file: `extract.py URL --schema products.json`
or inline: `extract.py URL --base "div.product-card" --field "title:h2.name:text" --field "url:a.link:attribute:href"`.

XPath instead of CSS: add `--xpath` and write XPath in `selector`
(`baseSelector: "//div[@class='product-card']"`, `selector: ".//h2"`).

## 2. Field types

| type | returns | notes |
|------|---------|-------|
| `text` | inner text | the default |
| `attribute` | one HTML attribute | requires `"attribute": "href"` etc. |
| `html` | inner HTML of the match | keep markup |
| `nested` | one sub-object | give it its own `fields` |
| `list` | array of simple values | repeated simple items |
| `nested_list` | array of objects | repeated complex items — the key to hierarchy |
| add `"default": ...` | fallback when selector misses | prevents nulls breaking rows |

### Nested / list example (category → many products → many reviews)

```python
{
  "name": "Catalog",
  "baseSelector": "div.category",
  "fields": [
    {"name": "category", "selector": "h2", "type": "text"},
    {"name": "products", "selector": "div.product", "type": "nested_list", "fields": [
        {"name": "name", "selector": "h3", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "features", "selector": "ul.feat li", "type": "list",
            "fields": [{"name": "feature", "type": "text"}]},
        {"name": "reviews", "selector": "div.review", "type": "nested_list", "fields": [
            {"name": "author", "selector": ".by", "type": "text"},
            {"name": "stars", "selector": ".rating", "type": "text"}]}
    ]}
  ]
}
```

## 3. Sibling selectors

When related data lives in an *adjacent* element (classic on table layouts like
Hacker News where the score is in the `<tr>` after the title row), use `source`:

```python
{"name": "score", "selector": "span.score", "type": "text", "source": "+ tr"}
```

`"source": "+ selector"` hops to the next sibling before applying the field
selector. (Note: for the HN example the modern layout puts title+link in the
same `tr.athing` row — the inline test in extract.py's docstring proves it.)

## 4. Regex patterns (rung 2)

Fastest possible extraction — pure pattern matching over the page content, no
selectors, no LLM. `extract.py URL --regex email,phone_us,url`.

Built-in pattern names (pass comma-separated, case-insensitive; the script maps
`phone_us`→`PhoneUS`, `date_us`→`DateUS`, `ipv4`→`IPv4`, etc.):

```
email, phone_intl, phone_us, url, ipv4, ipv6, uuid, currency, percentage,
number, date_iso, date_us, time_24h, postal_us, postal_uk, hex_color,
twitter_handle, hashtag, mac_addr, iban, credit_card
```

Output rows: `{"url","label","value","span":[start,end]}`.

**Important:** regex matches the page's *visible/rendered content*, not hidden
attributes. If a URL only exists in an `href` (not shown as text), use a CSS
`attribute` field instead. For custom patterns, edit the schema in code
(`RegexExtractionStrategy(custom={"sku": r"SKU:\s?(\w{6,8})"})`) — see
crawl4ai docs; the CLI covers the built-ins.

## 5. Authoring a schema cheaply (rung 4)

Two ways, both make future extraction free:

**A. Agent hand-writes it (── $0, preferred).**
```
gen_schema.py URL --sample --css "main"     # dumps trimmed HTML
```
Read the HTML, find the repeating container → that's `baseSelector`. Pick one
selector per datum you want → those are `fields`. Save as JSON. Done, no API
call. This is usually fast and the most reliable because you *see* the DOM.

**B. Let crawl4ai infer it (── one LLM call, then free).**
```
gen_schema.py URL --query "name, price, rating, url" --llm -o schema.json
```
Use when the DOM is large/confusing. The schema is validated against real HTML
before it's returned. **Save the file and never call this again for that site.**

### Tips for durable selectors
- Prefer stable hooks: `data-*` attributes, semantic classes, `href` patterns.
- Avoid `nth-child()` / positional selectors — they break when order changes.
- Give every field a `"default"` so one missing element doesn't drop the row.
- Test against the cache: fetch once, then re-run `--schema` free until it's right.

## 6. Gotchas

- **JS-rendered rows**: if the container appears only after JS, add
  `--wait "css:div.product-card"` (or `--js "window.scrollTo(0,document.body.scrollHeight)"`)
  so content loads before extraction.
- **Empty result / "no content extracted"**: selector didn't match, or the data
  is JS-loaded, or (for regex) the value isn't in visible text. Dump a sample
  with `gen_schema.py --sample` and check the real DOM.
- **One object, not a list**: still works — `baseSelector` can match a single
  container; you get a one-element array.

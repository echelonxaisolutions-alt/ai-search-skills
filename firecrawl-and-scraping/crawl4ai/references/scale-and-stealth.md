# Scale, concurrency, sessions & stealth

## Many URLs — use arun_many, never a loop

`scripts/batch.py` wraps `arun_many` with a dispatcher: ONE browser, a shared
page pool, adaptive concurrency, and automatic backoff. A shell loop of single
crawls re-launches the browser each time and hammers the server — slower and
ruder.

```bash
batch.py urls.txt -o out/ --concurrency 8 --min-delay 0.5 --max-delay 2.0
batch.py urls.txt -o out/ --schema products.json   # extract each URL instead of markdown
```

### Dispatchers
- **MemoryAdaptiveDispatcher** (what batch.py uses): watches RAM and pauses new
  tasks above `--mem-threshold` (default 85%), resuming when it drops. Prevents
  OOM on big jobs. `--concurrency` = `max_session_permit`.
- **SemaphoreDispatcher**: fixed hard concurrency cap, no memory awareness. Use
  when you want an exact simultaneous-request number.

### RateLimiter (built into batch.py)
`base_delay=(min,max)` random politeness delay between requests; exponential
backoff up to `max_delay` on 429/503; `max_retries=3`. Tune `--min-delay`
/`--max-delay` up for touchy servers, down for your own infra.

### Streaming
Both deep_crawl.py and batch.py stream (`stream=True`) — results are handled as
they complete, so you see progress and partial output survives a crash.

## Dynamic / JS-heavy pages

- `--wait "css:.results"` — wait until a selector appears before scraping.
- `--wait "js:() => window.dataReady === true"` — wait on a JS condition.
- `--js "window.scrollTo(0, document.body.scrollHeight)"` — run JS first (lazy
  load, infinite scroll, expand tabs). Pass a click loop to open accordions.
- `--magic` — magic mode: auto-dismiss overlays/cookie walls and simulate a real
  user. Cheap first thing to try when a page hides content behind a modal.

## Sessions & authenticated crawling

Reuse a logged-in browser profile across runs with a persistent user data dir:

```bash
scrape.py "https://app.site.com/dashboard" --profile "C:/crawl_profiles/site"
```

First run (add `--headed`) lets you log in manually; the cookies/localStorage
persist in that folder, so later headless runs are already authenticated. This
uses crawl4ai's managed-browser mode. Keep profile dirs out of git and treat
them as secrets — they contain live sessions.

## Proxies

`--proxy "http://user:pass@host:port"` on scrape.py / extract.py routes through a
proxy (rotate IPs, geo-target). Combine with `--stealth` for tougher targets.

## Stealth vs bot detection — escalation order

crawl4ai ships stealth patches (patchright + playwright-stealth). Try in order,
cheapest first:

1. `--magic` (dismiss overlays, light user simulation) — often enough.
2. `--stealth` (undetected browser patches) — beats basic fingerprinting.
3. `--stealth --proxy ...` (residential proxy) — for IP-based blocks.
4. **Switch to the `cloakbrowser` skill** — purpose-built to pass Cloudflare
   Turnstile, reCAPTCHA v3, FingerprintJS, BrowserScan. Use it when crawl4ai's
   stealth still gets blocked.
5. Paid **firecrawl** skills — last resort if you're willing to pay for a
   managed service that handles the hardest sites.

Respect robots/ToS and rate limits — politeness (delays, low concurrency) avoids
most blocks in the first place and keeps you off blocklists.

## Docker / server mode (advanced, optional)

crawl4ai ships a Dockerized FastAPI server (`crawl4ai` image) exposing crawl
endpoints with JWT auth — useful if you want crawling as a shared internal
service rather than in-process. Not needed for the CLI scripts here; reach for
it only when multiple machines/services need a central crawl API. See the
crawl4ai docs "Docker Deployment" page.

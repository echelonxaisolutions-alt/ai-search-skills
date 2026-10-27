---
name: cloakbrowser
description: Stealth Chromium browser that passes bot detection (Cloudflare Turnstile, reCAPTCHA v3, FingerprintJS, BrowserScan). Drop-in replacement for Playwright. Auto-trigger ANY time a task involves Chromium, Playwright, Puppeteer, web scraping, browser automation, anti-bot bypass, browsing past Cloudflare, scraping behind WAFs, agent-based browsing (browser-use, Crawl4AI, Scrapling, Stagehand, LangChain), or whenever stock Playwright would be considered. Auto-trigger phrases: scrape, browse, render, fetch this page, click, automate, playwright, puppeteer, chromium, bot detection, captcha, cloudflare, turnstile, fingerprint, blocked, anti-bot, headless, residential proxy.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# CloakBrowser — Default Stealth Browser

> Patched Chromium binary with 57 C++ source-level fingerprint patches. Same Playwright API. **3-line drop-in replacement.** Passes Cloudflare Turnstile, reCAPTCHA v3 (0.9 score), FingerprintJS, BrowserScan, ShieldSquare. Verified Apr 2026 against 30+ detection sites.
>
> **Use this instead of stock Playwright by default.** No downside — same API, same speed, more passes.

## When to invoke

Any time the task involves a Chromium browser:
- Scraping JS-rendered pages
- Filling forms / logging in / automating
- Fetching pages that 403 / Cloudflare / show CAPTCHA
- Running an agent framework (browser-use, Crawl4AI, Stagehand, Scrapling, LangChain web tools)
- Replicating what a human sees in a browser

**Do NOT use** for:
- Static HTML fetch — use `curl` or `firecrawl-scrape` (cheaper)
- GitHub repos — use `repo-learner` or `git clone`
- Auth-walled sites you don't have credentials for

## Install (one-time)

```bash
pip install cloakbrowser           # Python
# OR
npm install cloakbrowser playwright-core   # Node + Playwright
npm install cloakbrowser puppeteer-core    # Node + Puppeteer
```

First launch auto-downloads the ~200MB patched Chromium binary (cached at `~/.cloakbrowser/`).

## Python — the 80% case

```python
from cloakbrowser import launch

browser = launch()                       # headless, stealth default
page = browser.new_page()
page.goto("https://protected-site.com")
print(page.title())
browser.close()
```

Async:
```python
import asyncio
from cloakbrowser import launch_async

async def main():
    browser = await launch_async()
    page = await browser.new_page()
    await page.goto("https://example.com")
    print(await page.title())
    await browser.close()

asyncio.run(main())
```

## Node / Playwright

```javascript
import { launch } from 'cloakbrowser';

const browser = await launch();
const page = await browser.newPage();
await page.goto('https://protected-site.com');
await browser.close();
```

## Recommended config for stubborn sites

```python
browser = launch(
    proxy="http://user:pass@residential-proxy:port",  # residential, not datacenter
    geoip=True,         # match timezone/locale to proxy exit IP
    headless=False,     # headed mode + xvfb on Linux servers
    humanize=True,      # human-like mouse, keyboard, scroll
)
```

If a Linux server: install Xvfb first.
```bash
sudo apt install xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

## Persistent profile (login sessions, bypass incognito detection)

```python
from cloakbrowser import launch_persistent_context

ctx = launch_persistent_context("./my-profile", headless=False)
page = ctx.new_page()
page.goto("https://example.com")  # cookies + localStorage persist
ctx.close()
```

## Pin a fingerprint seed (returning visitor)

```python
# Same seed across runs = same device identity = looks like a real returning user
browser = launch(args=["--fingerprint=12345"])
```

## Quick test it's working

```bash
docker run --rm cloakhq/cloakbrowser cloaktest
# OR if installed locally:
python -m cloakbrowser info
```

## CLI utilities

```bash
python -m cloakbrowser install      # Pre-download binary
python -m cloakbrowser info         # Show version + path
python -m cloakbrowser update       # Check for newer binary
python -m cloakbrowser clear-cache  # Wipe cached binaries
```

## Runtime context (LOAD-BEARING — learned 2026-07-24)

**A stealth browser only passes DataDome-class WAFs from a NON-elevated, interactive desktop session.** Run the same launch from an elevated / detached / pm2 / Windows-service / session-0 context and DataDome silently serves **empty pages** — no captcha, no error, just zero results, which naive scrapers record as a false `no_results`.

- **Windows:** a normal user session (e.g. Task Scheduler "run only when user is logged on", RunLevel **Limited** / non-elevated). NEVER elevated pm2 or a Windows service. There is no xvfb equivalent — it needs a real logged-in desktop.
- **Linux servers:** headed + `Xvfb` (see below), non-root.
- **Unattended scraping MUST be canary-gated:** before trusting any empty result, look up a known-common name that must return records; empty canary → the context is soft-blocked → halt + alert, write nothing. A soft-block is `blocked`, never `no_results`. Never cache a negative across the process boundary.


## Common gotchas

| Symptom | Fix |
|---|---|
| Still blocked on Kasada / Akamai | Install Linux fonts: `sudo apt install fonts-noto-color-emoji fonts-freefont-ttf fonts-unifont` |
| reCAPTCHA v3 score below 0.5 | Use `time.sleep()` not `page.wait_for_timeout()` (CDP commands leak), use residential proxy, spend 15s+ on page |
| Site blocks fresh sessions but works after first visit | Use `launch_persistent_context()` + `args=["--disable-http2"]` on first run only |
| macOS Gatekeeper blocks binary | `xattr -cr ~/.cloakbrowser/chromium-*/Chromium.app` |
| `playwright install` doesn't help | You don't need it — CloakBrowser downloads its own binary. Only need `playwright install-deps chromium` |

## Framework integrations (browser-use, Crawl4AI, etc.)

CloakBrowser launches first, framework connects via CDP:

```python
from cloakbrowser import launch_async

browser = await launch_async(args=["--remote-debugging-port=9242"])
# Connect your framework to http://127.0.0.1:9242
```

Full reference: `knowledge_base/cloakbrowser/` (populated by repo-learner).

## Why use this over alternatives

| Tool | Patch Level | reCAPTCHA v3 | Cloudflare Turnstile | Engine |
|---|---|---|---|---|
| Stock Playwright | None | 0.1 (bot) | Fail | Chromium |
| playwright-stealth | JS injection | 0.3-0.5 | Sometimes | Chromium |
| undetected-chromedriver | Config patches | 0.3-0.7 | Sometimes | Chrome |
| Camoufox | C++ (Firefox) | 0.7-0.9 | Pass | Firefox |
| **CloakBrowser** | **C++ (Chromium)** | **0.9** | **Pass** | **Chromium** |

Source-level patches survive Chrome updates. JS-injection tools break on every Chromium release.

## Legal posture

Wrapper is MIT. Binary is free use, no redistribution (see `BINARY-LICENSE.md`). The maintainers explicitly prohibit unauthorized automation, credential stuffing, and account abuse. For legitimate use cases (research, public data, agent-driven browsing for legitimate operations) this is the correct tool.

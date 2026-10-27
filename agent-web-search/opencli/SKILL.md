---
name: opencli
description: Browser Bridge + CLI hub. Reuses your logged-in Chrome session to drive any website deterministically. 100+ built-in adapters (Reddit, HackerNews, Bilibili, Zhihu, Twitter/X, Xiaohongshu, GitHub, etc.) plus wrapped local CLIs (gh, docker, obsidian, tg, discord) and Electron app control (Cursor, ChatGPT, Antigravity). Zero LLM cost at runtime. Auto-trigger when the task involves driving a website while logged in, automating a workflow inside a real browser session, extracting data from a site that requires authentication, wrapping a local CLI through a unified surface, controlling an Electron desktop app, or writing a reusable site adapter. Trigger phrases include opencli, adapter, scrape my account, my logged-in session, drive my browser, run on my chrome, automate this site, write a CLI for, deterministic CLI, wrap this binary.
allowed-tools: Bash(opencli:*), Read, Edit, Write, Grep, Glob
---

# OpenCLI — Browser Bridge + CLI Hub

> Turn websites, browser sessions, Electron apps, and local tools into **deterministic CLIs** for humans and AI agents. Reuses your logged-in Chrome via a small extension + daemon. Zero LLM cost at runtime.

## When to reach for this

| You need | Use |
|---|---|
| Static HTML fetch | `curl` (free, instant) |
| JS-rendered scrape, public page | `firecrawl-scrape` |
| Anti-bot bypass, public page, no login | **CloakBrowser** |
| **Site requires my login session** (Twitter, Xiaohongshu, GitHub UI, my Notion) | **OpenCLI** |
| **Drive my Chrome with a stable CLI repeatedly** | **OpenCLI** |
| **Wrap a local binary as a CLI in one surface** | **OpenCLI** |
| **Control an Electron app** (Cursor, ChatGPT, Antigravity) | **OpenCLI** |

The unlock: **your credentials never leave Chrome.** OpenCLI doesn't store passwords or session cookies — it asks the extension to do work on the page you're already logged into.

## Install (one-time setup)

OpenCLI requires **Node ≥ 21** and a small Chrome extension. Install the CLI with `npm install -g @jackwener/opencli`.

Setup checklist:
```bash
opencli --version          # v1.7.22+ recommended
opencli doctor             # verify daemon + extension + Chrome connection
```

If `doctor` flags the extension missing:
1. Open `chrome://extensions` in the Chrome profile you want OpenCLI to drive
2. Either install **OpenCLI** from [Chrome Web Store](https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk)
3. Or load unpacked from the latest release zip

The daemon (HTTP bridge on port 19825) auto-starts when needed.

## Multi-profile Chrome

If you have multiple Chrome profiles (personal / work / client), install the extension in each, then:

```bash
opencli profile list
opencli profile rename <contextId> work
opencli profile use work
opencli --profile work browser state
```

With one profile, OpenCLI auto-selects it.

## 80% case — run a built-in adapter

```bash
opencli list                                    # see all 100+ adapters
opencli hackernews top --limit 5                # public, no login
opencli reddit hot --limit 10 --subreddit MCA   # public
opencli twitter user <handle>                   # needs your Twitter login
opencli xiaohongshu notifications               # needs Xiaohongshu login
opencli notion search "MCA leads"               # needs Notion login
```

Output is structured JSON or pipeable text — same shape every run, scriptable, CI-friendly. **No tokens consumed.**

## When the site isn't covered — write an adapter

Use the bundled `opencli-adapter-author` skill (already installed globally — Chinese-language by default, mixed English). It guides you end-to-end:

```bash
opencli browser <session> open <url>            # navigate
opencli browser <session> state                 # DOM snapshot (not screenshot)
opencli browser <session> click <selector>      # interact
opencli browser <session> network               # inspect XHR/fetch traffic
opencli browser <session> extract <selector>    # pull data
opencli browser recon analyze <url>             # one-shot site recon
opencli browser recon init <site>/<command>    # scaffold adapter
opencli browser recon verify <site>/<command>  # test before publish
```

Adapters land in `~/.opencli/clis/<site>/<command>/` and become reusable across sessions.

## Browser primitives (low-level, AI agent uses these)

`opencli browser` commands available: `open`, `state`, `click`, `type`, `fill`, `select`, `keys`, `wait`, `get`, `find`, `extract`, `frames`, `screenshot`, `scroll`, `back`, `eval`, `network`, `tab list`, `tab new`, `tab select`, `tab close`, `init`, `verify`, `close`.

Each `browser` command needs a `<session>` positional immediately after `browser`. Example:
```bash
opencli browser work open https://x.com/home
opencli browser work tab new https://google.com
opencli browser work tab list
opencli browser work click 'button[data-testid=login]' --tab <targetId>
```

## CLI hub — wrap a local binary

```bash
opencli external register gh        # now: opencli gh repo list ...
opencli external register docker
opencli external register longbridge
opencli external register tg        # Telegram CLI
```

Same discovery surface (`opencli list`), same scriptable output, your existing binary unchanged underneath.

## Electron app control

Drive Cursor, Codex, ChatGPT, Antigravity directly from the terminal via CDP. See `~/.claude/skills/opencli-browser/` and `opencli list` for available adapters.

## Companion skills (already installed globally)

| Skill | When to use |
|---|---|
| `opencli-adapter-author` | Operate a site live, or write a reusable adapter for a new site |
| `opencli-browser` | Direct browser automation reference |
| `opencli-autofix` | Repair a broken adapter that returns empty data |
| `opencli-usage` | Quick reference for all commands |

All four auto-trigger on more specific intents. This top-level `opencli` skill is for orientation + first decision.

## Why use this over Playwright / CloakBrowser

| Tool | Login state | Token cost | Setup | Determinism |
|---|---|---|---|---|
| Stock Playwright | Empty browser, no login | Free | Light | Per-script |
| CloakBrowser | Empty browser, stealth | Free | Medium (binary download) | Per-script |
| Firecrawl | No login | Paid per request | None | Per-request |
| **OpenCLI** | **Your real logged-in Chrome** | **Free** | **Medium (extension)** | **Adapter = stable contract** |

OpenCLI's advantage isn't stealth — it's **persistence of session + deterministic CLI surface**. Once an adapter is written, the same `opencli xiaohongshu notifications` works every day, no flakiness, no token cost.

## Common gotchas

| Symptom | Fix |
|---|---|
| Empty data from a built-in command | The site is logged out in Chrome. Open the site in Chrome, sign in, retry. |
| `opencli doctor` says extension not connected | Install OpenCLI extension in the active Chrome profile, restart Chrome. |
| Multiple profiles confusion | `opencli profile list` then `--profile <alias>` or `opencli profile use <alias>` |
| Adapter returns garbage on a site that worked yesterday | Site DOM changed. Run `opencli-autofix` skill. |
| Browser session disconnects mid-task | Add `--keep-tab true --window foreground` to keep the tab alive |
| Want to see what the browser is doing | Add `--trace on` — saves a trace artifact you can replay |

## Legal posture

MIT-licensed. Reuses YOUR logged-in session — no scraping behind credentials you don't have. Standard rule: don't use it to violate site ToS or do anything you wouldn't do manually. For research and automating workflows in your own accounts it's the right tool.

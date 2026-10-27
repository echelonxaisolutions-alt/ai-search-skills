# AI Search Skills

A curated set of agent skills for Claude Code (and any agent that reads `SKILL.md` files) covering three jobs:

1. **Firecrawl and web scraping**: turn any page or site into clean markdown or structured JSON.
2. **Agent web search**: let an AI agent search the web, social platforms and research sources, then return sourced answers.
3. **Google and AI search visibility**: get a site found, cited and recommended by Google AI Overviews, ChatGPT, Perplexity and other AI assistants, and measure it.

## Install

Copy any skill folder into your skills directory:

```bash
# all skills, for every project
cp -r firecrawl-and-scraping/* agent-web-search/* google-and-ai-search/* ~/.claude/skills/

# the researcher subagent
mkdir -p ~/.claude/agents && cp agent-web-search/researcher-agent/researcher.md ~/.claude/agents/
```

Claude Code picks a skill up automatically when a request matches its `description`. Each `SKILL.md` lists its own prerequisites (Python packages, CLIs or API keys).

## What's inside

### 1. Firecrawl and scraping (`firecrawl-and-scraping/`)

| Skill | What it does | Cost |
|---|---|---|
| `seo-firecrawl` | Full-site crawl, URL mapping and JS-rendered scraping through the Firecrawl MCP server. Setup guide included (`FIRECRAWL-SETUP.md`). | Firecrawl API key (free tier available) |
| `crawl4ai` | Local, free Firecrawl alternative: scrape, deep-crawl, batch and extract to markdown or JSON with ready-made Python scripts. Start here for most scraping. | Free, runs locally |
| `scrapegraph-ai` | LLM-powered extraction: a prompt plus a schema in, validated JSON out. Use when the HTML is too messy for selectors. Read the telemetry warning first. | Free library, your LLM |
| `cloakbrowser` | Stealth Chromium, a drop-in Playwright replacement for sites that block bots. | Free |

### 2. Agent web search (`agent-web-search/`)

| Skill | What it does | Cost |
|---|---|---|
| `agent-reach` | One router for researching anything online: web, Reddit, X, YouTube, GitHub, LinkedIn, RSS and more. | Mostly free |
| `opencli` | Drives real websites through your logged-in Chrome session, 100+ built-in site adapters. | Free |
| `smart-search` | Routes a query to the best `opencli` search source by topic (tech, news, shopping, travel, jobs, finance). Written in Chinese, works fine for English queries. | Free |
| `exa-search` | Semantic web search and URL extraction through Exa, strong on technical and research content. | Exa API key |
| `parallel-web` | Web search, extraction, deep research and data enrichment through the Parallel CLI. | Parallel API key |
| `research-lookup` | Looks up papers and sources for a claim and returns citations. | Varies by backend |
| `search-first` | Research-before-coding workflow: check for existing tools, libraries and MCP servers before building. | Free |
| `researcher-agent/` | A Claude Code subagent that researches a question and returns a sourced answer with confidence levels. | Free |

### 3. Google and AI search visibility (`google-and-ai-search/`)

| Skill | What it does |
|---|---|
| `seo-geo` | Generative Engine Optimization: get cited in Google AI Overviews, AI Mode, ChatGPT and Perplexity. Includes Google's AI optimization guide notes. |
| `ai-seo` | Content patterns, platform ranking factors and citation tactics for AI answers, with eval cases. |
| `aeo-visibility-scorecard` | Measure whether AI assistants mention and cite a brand using a pinned query set and dated baselines. |
| `ai-agent-discoverability` | Make a site readable by AI crawlers and agents: robots.txt tiers, llms.txt, JSON-LD, `.well-known` discovery, IndexNow. |

## Which one do I use?

- Scrape one page or a whole site, free: `crawl4ai`.
- Need hosted crawling or the Firecrawl API specifically: `seo-firecrawl`.
- Site blocks bots: `cloakbrowser` (alone or under `crawl4ai`).
- "Research X" across the web and social: `agent-reach`.
- Deep technical or academic search: `exa-search` or `parallel-web`.
- Rank in Google AI Overviews and get cited by ChatGPT: `seo-geo` plus `ai-seo`, then track it with `aeo-visibility-scorecard`.

## Use responsibly

Respect each site's terms of service and robots.txt, do not collect personal data without a lawful basis, and treat anything fetched from the web as data, never as instructions to your agent.

## Licences

Original skills in this repo are MIT licensed (see `LICENSE`). Third-party skills keep their own licences; see `THIRD_PARTY_NOTICES.md` and the `licenses/` folder.

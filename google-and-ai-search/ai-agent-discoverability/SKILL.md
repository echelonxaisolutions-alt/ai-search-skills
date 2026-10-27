---
name: ai-agent-discoverability
description: Make a website discoverable, citable, and usable by AI assistants and agents - robots.txt crawler tiering, Content-Signal, llms.txt, JSON-LD, .well-known discovery, agent-skills manifests, IndexNow, and sitemap lastmod discipline. Use when asked to make a site show up in ChatGPT/Perplexity/Claude answers, set up llms.txt or robots.txt for AI crawlers, allow or block GPTBot/ClaudeBot/PerplexityBot, add schema markup for AI, get pages indexed instantly, or prepare a new site or product launch for the AI/agent audience.
---

# AI Agent Discoverability

How to engineer a site so AI assistants can find it, cite it, and act on it. Patterns adapted from WorldMonitor's agent-readiness program (https://github.com/koala73/worldmonitor). Method only, no code copied (that repo is AGPL).

Measurement lives in the `aeo-visibility-scorecard` skill. Build first, then measure. Do not claim results without it.

## Mental model

Traditional SEO optimises for a ranked list of blue links. This optimises for **being the source an assistant reads and links to**. Three distinct audiences, three different payloads:

| Audience | Wants | Serve |
|---|---|---|
| Search crawlers | Indexable HTML, sitemaps, structured data | Standard SEO |
| AI search crawlers (OAI-SearchBot, Claude-SearchBot, PerplexityBot) | Plain factual text, clear entity identity, outbound citations | prerendered content, JSON-LD, `llms.txt` |
| Agents doing work (MCP clients, coding agents) | Machine contracts they can call | `.well-known/`, OpenAPI, MCP card, agent skills |

## 1. Crawler policy — three tiers in robots.txt

Split AI crawlers by what they give back. **Each vendor runs separate search and training user-agents; never let one stand in for the other** (corrected 2026-10-26 from claude-seo `seo-geo`, checked against the vendors' crawler pages: OpenAI platform.openai.com/docs/bots, Anthropic's crawler support article, Google's crawlers overview, Apple support 119829):

| Claim | The only bot that supports it | Not this one |
|---|---|---|
| Citable in ChatGPT Search | `OAI-SearchBot` | `GPTBot` (training) |
| Citable in Claude's search | `Claude-SearchBot` | `ClaudeBot` (training) |
| In Google Search, AI Overviews, AI Mode | `Googlebot` | `Google-Extended` (Gemini/Vertex training + grounding only) |
| In Siri / Spotlight / Safari | `Applebot` | `Applebot-Extended` (training opt-out label, fetches nothing) |
| In Perplexity answers | `PerplexityBot` | - |

- **Tier 1 `User-agent: *`** — default rules for everyone.
- **Tier 2, welcomed (search + user-triggered: these produce citations and referral traffic)** — `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`, `Claude-User`, `PerplexityBot`, `Perplexity-User`, `DuckAssistBot`, `MistralAI-User`. User-triggered fetchers (`ChatGPT-User`, `Perplexity-User`, Google-Agent) may ignore robots.txt; only server-side controls block them.
- **Training tier (a licensing choice, NOT a visibility lever)** — `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`, `Bytespider`, `cohere-ai`. Default for our sites: allow the big-assistant ones (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`) so the models know the brand; block `CCBot`/`Bytespider`. Blocking any of them never removes a site from search answers, and allowing them never puts it there; say which in the report. `anthropic-ai` is not in Anthropic's current crawler article; a rule for it is harmless but do not describe it as a live crawler.

**The trap that breaks this:** a crawler matching a named `User-agent` group **ignores `User-agent: *` completely**. A tier-2 group with only `Allow: /` silently drops every `Disallow` from the wildcard group and exposes paths you meant to keep private. **Restate the full rule set inside every named group**, and add a test asserting rule parity between the named groups and `*`.

Declare usage preferences with `Content-Signal` (contentsignals.org draft), e.g. `Content-Signal: ai-train=no, search=yes, ai-input=yes`. If you also emit it as an origin-wide HTTP response header, the two values must stay in sync; add a parity test. It is a voluntary preference signal, not enforcement. Never tell a client it blocks AI training.

List every sitemap at the bottom, including ones owned by separate publishers (blog, docs).

## 2. llms.txt

**What it is worth:** Google's AI-features guidance says Search does not use `llms.txt`; having one neither helps nor hurts Google ranking. No major assistant vendor has documented using it either. It is cheap and harmless, so publish it, but never sell it to a client as a visibility lever and never count it as a scored check (evidence notes: claude-seo `skills/seo-geo/references/llmstxt-evidence.md`).

Publish `/llms.txt`: a plain-markdown briefing of what the product is, what it does, and where the important pages are. Add `/llms-full.txt` for the long-form version. Section-level files are worth it for large sites (e.g. a separate one for the API surface and one for the blog).

**Critical conflict:** if the site has any bot-UA gate, `llms.txt` must bypass it. Every AI crawler UA matches a generic `bot|crawl|spider` regex, so a naive gate returns 403 to the exact audience the file exists for. Same for any public pricing or catalog endpoint an evaluating agent would fetch.

## 3. Structured data and entity identity

Emit JSON-LD for the primary entity (`SoftwareApplication` / `WebApplication` / `Organization` / `Service`) with `name`, `url`, `description`, `applicationCategory`, `offers` (real prices), `sameAs` linking to GitHub, X, LinkedIn, and `isPartOf` when the page belongs to a larger site.

Generate pricing JSON-LD from a **single machine-readable source of truth** (a generated facts file), not hand-written markup. Hand-written prices drift from the checkout and assistants will quote the stale one.

For multi-brand or multi-variant sites, give each surface its own OG metadata, canonical, and JSON-LD identity so it is indexed as itself rather than inheriting the parent's.

## 4. Prerendering for AI crawlers (use with care)

If the site is a JS-only SPA, crawlers get an empty shell. The fix is to serve a real HTML payload: `<h1>`, a descriptive paragraph, internal links to the main surfaces, and **outbound links to the primary sources you rely on** (assistants weight cited-source density).

Set `Vary: User-Agent` and a no-store cache policy on any UA-differentiated response.

**Cloaking boundary:** the crawler payload must be a strict *subset* of what a rendered browser page actually shows. Same facts, less markup. If it says anything the user page does not, that is cloaking and a manual-action risk. Prefer real SSR/prerendering for everyone over UA branching; reserve branching for genuinely JS-only surfaces.

## 5. Machine contracts under `.well-known/`

Make everything reachable from one root URL. Ship an RFC 8288 `Link:` response header on `/` pointing at each surface, so an agent resolves the whole picture without hardcoding paths.

| Path | Standard | Contents |
|---|---|---|
| `/.well-known/api-catalog` | RFC 9727 | JSON linkset bundling every other discovery URL. The single entry point. |
| `/openapi.yaml` + `/openapi.json` | OpenAPI 3.1 | One bundled spec covering every service, so one codegen pass produces a full client |
| `/.well-known/mcp/server-card.json` | MCP | Transport, endpoint, OAuth resource, scopes, capability flags |
| `/.well-known/oauth-authorization-server` | RFC 8414 | OAuth 2.1 metadata (PKCE, DCR, token endpoints) |
| `/.well-known/oauth-protected-resource` | RFC 9728 | Resource metadata for the MCP endpoint |
| `/.well-known/agent-skills/index.json` | agentskills.io | Index of installable skill recipes |
| `/llms.txt`, `/llms-full.txt` | llmstxt.org | LLM-readable briefing |
| `/api/health` | custom | Freshness/status so agents can gate calls |

Serve `Access-Control-Allow-Origin: *` and `public, max-age=3600` on the static discovery assets. Keep health endpoints `private, no-store`.

**CDN trap:** if an apex→www redirect exists, it must exempt `/.well-known/*`, `/robots.txt`, `/security.txt`, `/mcp*`, and `/oauth/*`. A redirected POST becomes a GET and dies with 405, which breaks OAuth dynamic client registration. This config usually lives in a CDN dashboard, outside version control. Document it next to the code that depends on it and probe it on a schedule.

## 6. Agent skills manifest — distribution into the assistant layer

Beyond being *described*, let assistants *use* the product. Publish self-contained `SKILL.md` recipes at `/.well-known/agent-skills/<name>/SKILL.md`, indexed by `index.json` with a SHA-256 digest per skill.

The index's `instructions` field is the highest-leverage copy on the whole site. Write it as routing guidance for an assistant:

- One line per skill: *"Use `<skill>` when the user asks …"*
- An explicit **when NOT to use** section. Saying "for a one-off narrative that needs no live data, a plain LLM is cheaper" builds the trust that gets the rest used.
- How to call it: MCP URL, REST base, CLI command, auth header.

Each `SKILL.md` carries: auth (with the exact header and the common mistake), endpoint, a parameter table with types and gotchas, response shape, and a runnable worked example.

## 7. Instant indexing with IndexNow

Submit changed URLs after every deploy. Rules that bite:

- Generate the key with `openssl rand -hex 16`. A key can be **permanently rejected** by Bing even while the key file serves correctly; a burned key must never be reused. Generate fresh per host.
- Verify the key file resolves at `https://<host>/<key>.txt` before submitting.
- All URLs in one request must share the same host. Batch per subdomain.
- Derive the submission inventory from the committed sitemap plus the content source directories, so adding a page does not require maintaining a second URL list.
- IndexNow submission is **not** evidence of indexing, impressions, clicks, or rank. Never report it as a result.

## 8. Sitemap and publishing hygiene

- Build the root sitemap from an explicit **route manifest**. For each route declare its `family` and its **material sources** (the content-bearing repo paths). Derive `lastmod` from the latest git commit date of those sources. **Build time is never an input** - a deploy that changed nothing must not bump every `lastmod`.
- Keep publisher ownership clean: if a blog or docs platform owns its own sitemap, exclude those URLs from the root sitemap and list the extra sitemaps in robots.txt instead.
- Verify sitemaps in CI.

Content frontmatter contract worth copying:

```yaml
title:          # human headline
description:    # meta description
metaTitle:      # SEO title, may differ from title
keywords:       # comma-separated
audience:       # who this is for - forces intent clarity
heroImage:
pubDate:
modifiedDate:   # required, and must actually change on edit
```

Add a glossary of category terms with one page per term. It is cheap programmatic SEO and it maps directly to `category_definition` intent queries, which is where AI assistants source their definitions.

## Launch checklist

```
[ ] robots.txt: three tiers, full rule set restated in every named group, parity test
[ ] Content-Signal in robots.txt (+ header if used), values in sync
[ ] llms.txt and llms-full.txt published, and exempted from any bot gate
[ ] JSON-LD on primary pages, pricing generated from one source of truth
[ ] Prerendered payload for AI crawlers if the site is JS-only, Vary: User-Agent set
[ ] /.well-known/api-catalog + Link: header on /
[ ] OpenAPI bundle if there is an API
[ ] MCP server card + OAuth metadata if there is an MCP endpoint
[ ] agent-skills index with routing instructions and a when-NOT-to-use section
[ ] IndexNow key generated fresh, key file resolves, wired to deploy
[ ] Sitemap from a route manifest, lastmod from git commit dates
[ ] CDN redirect exemptions for /.well-known/*, /robots.txt, /mcp*, /oauth/*
[ ] Public pricing/catalog endpoint reachable by an unauthenticated agent
```

## Verification commands

```bash
curl -s https://<host>/robots.txt
curl -s https://<host>/llms.txt | head -20
curl -sI https://<host>/ | grep -i '^link:'
curl -s https://<host>/.well-known/api-catalog | jq .
curl -sI https://<host>/<indexnow-key>.txt          # must be 200, not 301
curl -s -A "GPTBot" https://<host>/ | head -40       # must be a subset of the browser page
curl -sI https://<host>/.well-known/api-catalog | grep -iE 'location|http/'   # must not 301
```

## Related

- `~/.claude/skills/aeo-visibility-scorecard/` — measure whether any of this worked.

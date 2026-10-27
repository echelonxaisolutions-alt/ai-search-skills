---
name: aeo-visibility-scorecard
description: Measure whether a brand is mentioned and cited by AI assistants (ChatGPT, Perplexity, Google AI Overview, Copilot) using a pinned query set, dated baselines, and honest missing-data handling. Use when asked about AEO, GEO, LLM SEO, AI search visibility, AI citations, "are we showing up in ChatGPT", "do AI assistants recommend us", tracking AI-referred traffic, or running a monthly/quarterly AI-visibility review. Also use before claiming any AI-visibility improvement, to check the claim is comparable.
---

# AEO / AI-Citation Visibility Scorecard

Method for measuring whether AI assistants mention and cite a brand, and whether that produces product outcomes. Adapted from the WorldMonitor measurement contract (worldmonitor repo, `docs/research/seo-ai-visibility/`). Method only, no code copied (that repo is AGPL).

## The one rule that makes this real

**A missing data source stays `Unavailable`. It never becomes a zero, and it never becomes a site-wide score.**

Every vendor "AI visibility score" collapses four unrelated things (traditional search, AI answers, referrals, conversions) into one number, which hides which one is broken. Keep them separate. A cell with no data says so.

Corollary: report **observation counts alongside rates**. "100% mention rate" on one observation is not a finding. Write `100% (1/1)`.

## Four separated layers

| Layer | What it measures | Source |
|---|---|---|
| Traditional search | Indexation, impressions, clicks, CTR, average position | Search Console / Bing Webmaster export |
| AI answers | Brand mention, direct citation, competitors cited, sentiment, accuracy | Manual observation panel |
| Referrals | Sessions by referrer family | Analytics export |
| Product outcomes | Pricing views, sign-ups, conversions, activations | Analytics + commerce |

Never let a citation-only change be presented as traffic, sign-up, or revenue uplift.

## Workflow

### 1. Build the query set (once, then freeze)

Write real decision queries a buyer would type, not keyword strings. Each entry gets: `id`, `query` (exact text), `intent`, `targetAudience`, `targetPage` (family + URL), `conversionGoal`, and `referenceEntities` (named competitors and primary sources to watch for in answers).

Cover five intents evenly:

| Intent | Example shape |
|---|---|
| `category_definition` | "best <category> for <job>", "what is <category>" |
| `use_case` | "how do I <job to be done>" |
| `developer_agent` | "<category> API / MCP / integration" |
| `evaluation` | "<brand> vs <competitor>", "is <brand> worth it" |
| `branded_entity` | "<brand> pricing", "what does <brand> do" |

**Start at 8-10 queries, not 25.** Each query costs 4 manual observations per period. WorldMonitor set 25 and their first baseline covered 1. Scale only after two clean cycles.

Assign page families (homepage, blog, docs, pricing, tools, etc.) so results roll up by surface, not just by query.

**Freeze it.** Hash the query set (query text, intent, target, conversion goal, reference entities) and store the digest with every baseline. If a comparison-critical field changes, that is a **new query set with a new ID and a new baseline series**. Never reinterpret old observations under new query definitions.

### 2. Run the manual AI panel

Run the **exact query text, unparaphrased**, on each of: ChatGPT Search, Perplexity, Google AI Overview/AI Mode, Copilot Search.

Fix and record the conditions before starting: UTC timestamp, country, locale, device, signed-in state. Use a clean signed-out profile. Google signed-in is personalised and contaminates comparison; if you must use it, record that as a limitation.

For each observation record:

- **Mention** — brand named anywhere in the answer.
- **Direct citation** — only when a visible answer link resolves to your host. A mention without a link is not a citation. This distinction is the whole point.
- All visible cited URLs, and which competitors were cited.
- Sentiment (positive / neutral / negative / mixed).
- Accuracy (accurate / mixed / inaccurate / unverified) plus any claim needing correction.
- Platform limitations or personalisation observed.

If a platform is unavailable, record status + reason and omit the observation. Never substitute a different surface and label it as the requested one. Never record collapsed or hidden content you did not actually expand.

Do not save account identifiers, precise location, unrelated history, or personal prompt content.

### 3. Pull first-party exports

Read-only exports only. **Do not scrape search result pages.**

- Search Console / Bing Webmaster: trailing 28-day and 90-day windows, grouped by query and by page. Join to the query set by **exact query text**; unknown queries fail closed.
- Analytics: aggregate rows grouped only by referrer family and landing-page family. No prompt text, no user-level events.
- Strip property IDs, tokens, and credentials before anything is written to a baseline.

Referrer families to track: `chatgpt`, `perplexity`, `google_search_ai`, `copilot_bing`, `claude`, `other_ai_search`, `unknown_direct`.

Outcome funnel: `sessions → dashboardLaunches (or primary-surface landings) → pricingViews → signUps → conversions → activations → apiActions`. Count **successful** events only; attempts stay in separate telemetry.

Preserve inbound UTM attribution. Pick an internal tag param that does not collide with an existing affiliate/referral param on the site.

Every provider window must end on or before the baseline's `observedAt`.

### 4. Write the dated baseline

One JSON file per period: `baselines/YYYY-MM-DD.json`. It holds source availability (`available` / `partial` / `unavailable` + reason), the search and referral windows, the manual observations, the query-set digest, the collection context, and a prioritised opportunity queue.

Copy the prior baseline to a new date and replace only observations and values. **Never edit a past observation in place.** New evidence moves the baseline timestamp forward; it never gets backdated into an earlier scorecard.

### 5. Render the scorecard and compare

Generate a markdown report with: collection context and limitations, data availability table, per-intent rollup, per-page-family rollup, referral/outcome table, and the experiment queue.

A month-over-month comparison is only valid when **all** of these hold:

- Same query-set ID and digest.
- Same collection geography, locale, device, and signed-in schedule.
- Both provider windows have supported data, and the current window's start **and** end both advance beyond the previous.
- Periods are in forward order.

If any fails, the periods are not comparable. Say so; do not present the delta.

Report separately:
- New and lost **direct citations** (same query + platform + context observed in both periods, citation state changed).
- Newly observed and no-longer-observed query/platform combinations (coverage change, not performance change). Collapsing these two is the most common way sparse audits fake a win.

Thresholds are diagnostics, not causal claims. A single answer, citation, or traffic change never proves uplift.

### 6. Decide what to build next — the expansion gate

Do not add a content or page family because a vendor score or one AI answer suggested it. Expansion requires **all four**:

1. Evidence of search or customer demand.
2. Healthy indexation of what already exists.
3. Useful engagement, not undifferentiated traffic.
4. A credible handoff into the product, pricing, API, or booking surface.

## Directory layout

```
research/aeo-visibility/
  query-set.json              # frozen, digest-pinned
  baselines/YYYY-MM-DD.json   # one per period, append-only
  scorecards/YYYY-MM-DD.md    # generated report
```

## Reporting to the operator

Lead with what is actually known. Example shape:

> Period 2026-08-27. AI panel: 32/40 observations (Copilot unavailable in 2 runs, reason recorded). Mention rate 44% (14/32), direct-citation rate 12% (4/32). Search Console: available, 28d impressions +18% vs prior window. Referrals: unavailable, no analytics export this cycle. Comparison to 2026-07-27 is valid (same digest, same context). Citation gain of 3 is real; the impression change cannot be attributed to it.

Never render an aggregate score that hides an unavailable source.

## Related

- `~/.claude/skills/ai-agent-discoverability/` — the build side. This skill measures; that one makes the site citable.

---
name: ui-automation-tool-research
description: Research UI/RPA automation tools (e.g. UiPath, Automation Anywhere, Power Automate, Selenium, Playwright, Blue Prism, WorkFusion) on the web and produce a comparison covering features, pricing, and market position, with citations for every claim. Use this whenever the user asks to research, compare, evaluate, or shortlist UI automation, RPA, or test automation tools, wants a vendor comparison for automation tooling, or asks "what's out there" for automating a UI-based process. Trigger even if the user doesn't say "RPA" explicitly — phrases like "automation tool options", "compare UiPath and Automation Anywhere", "which tool should we use to automate this UI workflow" all qualify.
---

# UI Automation Tool Research

Research web-based UI automation / RPA tools and produce a structured, cited comparison. Every factual claim (a feature, a price, a market-share or ranking statement) must be traceable to a source found during research — this is a comparison document, not a matter of opinion, so unsupported claims undermine the whole deliverable.

## When to use this

Use whenever the user wants an informed view of UI automation tooling: choosing a tool for a new automation initiative, refreshing knowledge of the vendor landscape, checking whether a specific tool fits their use case, or building a shortlist to bring to a decision-maker.

## Workflow

1. **Clarify scope only if genuinely unclear.** If the user already named tools (e.g. "compare UiPath, Power Automate, and Automation Anywhere") or gave a clear use case, proceed straight to research — don't stall on a clarifying question when the ask is clear. If scope is wide open ("research UI automation tools"), it's fine to pick a sensible default set of leading tools (e.g. UiPath, Automation Anywhere, Microsoft Power Automate, Blue Prism, Selenium, Playwright) rather than blocking on a question, but note the assumption to the user.

2. **Research each tool on the web**, gathering information on exactly these three points:
   - **Features** — what the tool automates (desktop/web UI, attended vs. unattended bots, AI/computer-vision capabilities, low-code vs. code-first, integrations, scalability).
   - **Pricing** — licensing model (per-bot, per-user, consumption-based), whether a free/community tier exists, and approximate published pricing if publicly available (note clearly when a vendor doesn't publish pricing).
   - **Market position** — relative standing (e.g. analyst reports like Gartner/Forrester if referenced by sources, market share signals, notable customers, recent funding/acquisition news, general reputation among practitioners).

   Use live web search for each point per tool — pricing and market position shift often enough that stale knowledge is unreliable. Prefer vendor sites for features/pricing and independent sources (analyst write-ups, review sites like G2/Capterra, tech press) for market position.

3. **Track sources as you go.** For each fact gathered, keep the URL and page title. Don't wait until the end to reconstruct citations — attach them at the point of research.

4. **Write the comparison**, organized by tool, covering all three points per tool, and add a short synthesis (which tool fits which scenario) if the user's use case is known.

5. **Cite every factual claim.** End with a "Sources" section listing every URL used, and inline-attribute specific figures (e.g. pricing numbers, market-share stats) to their source rather than leaving them floating. If a claim can't be sourced, either drop it or explicitly flag it as unverified — never present an unsourced number as fact.

## Output format

Default to a prose-and-headers write-up in the reply (or a Doc/Markdown file if the user wants something to keep or share — follow the standard artifact/file rules for that). Structure:

```
# UI Automation Tool Comparison

## <Tool Name>
Features: ...
Pricing: ...
Market position: ...

(repeat per tool)

## Summary
(short synthesis / recommendation if a use case was given)

## Sources
[Title](URL)
[Title](URL)
...
```

Keep prose tight — this is a reference document, not marketing copy. Flag anything time-sensitive (pricing, rankings) with the date it was retrieved, since these change.

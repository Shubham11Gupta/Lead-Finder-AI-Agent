# Lead Finder AI Agent

An AI-assisted prospecting system to find relevant people/customers/users for a startup, company, or shop, and help draft personalized outreach emails based on how the business can support their goals.

## Initial Goal

Build this project as a learning-first AI agent system where I:
- discover relevant potential customers from multiple online platforms (through allowed/official methods),
- evaluate how well each lead matches a target customer profile,
- generate personalized outreach email drafts,
- keep a human review step before any email is sent.

I am building this myself to deeply learn:
- AI agent design,
- data collection and normalization,
- lead scoring logic,
- LLM-based personalization,
- safe and compliant outreach workflows.

## Scope (Phase 1)

- Define Ideal Customer Profile (ICP) and targeting criteria.
- Integrate 1-2 data sources (APIs or compliant data inputs).
- Normalize lead data into a common schema.
- Score lead relevance.
- Draft outreach emails with clear reasoning.
- Human-in-the-loop approval queue (no fully autonomous sending).
- Store logs for learning and iteration.

## Non-Goals (for now)

- Fully autonomous mass emailing.
- Bypassing platform policies or scraping restricted/private data.
- Advanced multi-agent orchestration before core pipeline works.

## Guiding Principles

- Relevance over volume.
- Human approval before sending.
- Compliance and respect for user privacy.
- Transparent reasoning for why a lead was selected.
- Continuous improvement from feedback.

## High-Level Workflow

1. Input business context + ICP.
2. Collect candidate leads from approved sources.
3. Normalize and enrich lead records.
4. Score relevance.
5. Generate personalized outreach draft.
6. Human review (approve/edit/reject).
7. Send + track outcomes.
8. Learn from outcomes and improve scoring/prompting.

## Planned Project Structure

```text
lead-finder-ai-agent/
  README.md
  docs/
  src/
    connectors/
    scoring/
    personalization/
    orchestrator/
    review/
    sender/
    storage/
  tests/

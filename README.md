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

## Scope (Current)

- Define Ideal Customer Profile (ICP) and targeting criteria.
- Integrate 1-2 data sources (APIs or compliant data inputs).
- Normalize lead data into a common schema.
- Score lead relevance.
- Draft outreach emails with clear reasoning.
- Automated sending support through SMTP (email channel).
- Store logs for learning and iteration.

## Current Constraints

- No spam blasting or policy-unsafe scraping.
- Bypassing platform policies or scraping restricted/private data.
- Advanced multi-agent orchestration before core pipeline works.

## Guiding Principles

- Relevance over volume.
- Human approval before sending.
- Compliance and respect for user privacy.
- Transparent reasoning for why a lead was selected.
- Continuous improvement from feedback.

## High-Level Workflow (Automated)

1. Input business context + ICP.
2. Collect candidate leads from approved sources.
3. Normalize and enrich lead records.
4. Score relevance.
5. Generate personalized outreach draft.
6. Enrich public contact data (email discovery from public pages).
7. Generate outreach drafts.
8. Auto-send eligible email drafts (if enabled).
9. Save run outputs to `runs/<run_id>/`.

## Run It

1. Copy config:
```powershell
Copy-Item src\config\app.config.example.json src\config\app.config.json
```
2. Fill `src/config/app.config.json` with:
- `sources.serper_api_key`
- SMTP fields in `send` section
3. Dry run (no sending):
```powershell
python run_agent.py --config src/config/app.config.json
```
4. Enable sending:
- set `"send.enabled": true`
- run the same command again

## Project Structure

```text
lead-finder-ai-agent/
  README.md
  run_agent.py
  docs/
  src/
    connectors/
    orchestrator/
    sender/
    reply/
    scoring/
  tests/

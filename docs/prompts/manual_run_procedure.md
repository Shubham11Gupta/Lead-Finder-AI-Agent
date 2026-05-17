# Manual Run Procedure (Operator SOP)

## Purpose (in simple words)
This file is your daily playbook.  
It tells you exactly how to run the lead workflow manually with AI:
1. find possible brands
2. clean their data
3. score who is worth contacting
4. draft first-touch messages
5. review and send manually
6. classify replies for handoff

No automated follow-up is included.

## What Each Prompt File Is For
1. `00_system_role_prompt.md`: sets AI behavior and safety rules for the whole session.
2. `01_collection_extraction_prompt.md`: converts messy internet notes into clean lead JSON.
3. `02_scoring_prompt.md`: gives each lead a score and priority bucket (`A`, `B`, `skip`).
4. `03_outreach_draft_prompt.md`: creates first-touch outreach drafts.
5. `04_review_gate_prompt.md`: quality-checks each draft before sending.
6. `05_reply_classification_prompt.md`: classifies inbound replies and next manual action.

## Before You Start
1. Keep your ICP and targeting docs ready:
   - `docs/targeting-spec.md`
   - `docs/lead-scoring-spec.md`
   - `docs/lead-data-schema.md`
2. Create a run folder for today, for example:
   - `runs/2026-05-17/`
3. Prepare to save JSON outputs after each step.

## Run Steps (Manual Mode)
1. Start a fresh AI chat and paste `00_system_role_prompt.md`.
2. Collect raw evidence from allowed sources (search, Instagram bio/posts, brand site/about/contact, ad signals, etc.).
3. Paste `01_collection_extraction_prompt.md`, add your raw evidence, and get normalized leads JSON.
4. Save output as `runs/<date>/01_collected_leads.json`.
5. Remove obvious duplicates and incomplete junk leads manually.
6. Paste `02_scoring_prompt.md`, pass the cleaned leads JSON, and get scored output.
7. Save output as `runs/<date>/02_scored_leads.json`.
8. Keep only leads in bucket `A` and `B` with reachable channels.
9. Paste `03_outreach_draft_prompt.md` with those leads and generate first-touch drafts.
10. Save output as `runs/<date>/03_draft_queue.json`.
11. For each draft, run `04_review_gate_prompt.md`.
12. If rejected, use revised draft and re-check until approved.
13. Send approved messages manually from your actual channel (email/Instagram/WhatsApp).
14. Record send status in your run notes (sent/not sent, channel, timestamp).
15. When replies come in, run `05_reply_classification_prompt.md`.
16. Save reply output as `runs/<date>/04_reply_classification.json`.
17. Handoff `positive` replies to founder/sales manually. Do not auto-generate follow-ups.

## Suggested Daily Output Files
1. `01_collected_leads.json`
2. `02_scored_leads.json`
3. `03_draft_queue.json`
4. `04_reply_classification.json`
5. `operator_notes.md` (manual notes: what worked, what failed, what to improve)

## Quality Checks (Quick)
1. Never send without review gate approval.
2. Never claim fake numbers, fake partnerships, or guaranteed outcomes.
3. If a field is unknown, keep it as `unknown` and move on.
4. Prefer fewer high-quality leads over many weak leads.

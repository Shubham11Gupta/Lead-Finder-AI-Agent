# AI Instruction Pack (Manual Mode)

## Purpose
This folder contains ready-to-use prompts so you can run the lead workflow manually with an AI assistant before full automation.

## Files
1. `00_system_role_prompt.md` - set behavior and boundaries once per session.
2. `01_collection_extraction_prompt.md` - extract normalized leads from internet evidence.
3. `02_scoring_prompt.md` - score each lead (`A`, `B`, `skip`) with reasons.
4. `03_outreach_draft_prompt.md` - generate first-touch outreach drafts.
5. `04_review_gate_prompt.md` - approve/reject draft quality.
6. `05_reply_classification_prompt.md` - classify inbound replies and route action.
7. `manual_run_procedure.md` - day-to-day operator SOP.

## Manual usage order
1. Start new AI chat/session.
2. Paste `00_system_role_prompt.md` first.
3. Follow `manual_run_procedure.md` step by step.
4. At each stage, use the matching prompt file.

## Scope lock
1. First-touch outreach only.
2. No automated follow-up generation.
3. Manual founder/team handoff after reply.

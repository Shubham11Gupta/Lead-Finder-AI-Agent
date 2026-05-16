# Outreach Module (Step 19)

This module generates first-touch outreach drafts from scored leads.

## Main entrypoint
`OutreachDraftEngine.run(leads, run_context=...)`

## What it does
1. Filters to eligible leads (`priority_bucket` in `A/B`, `outreach_status=not_started`).
2. Selects best channel (email -> Instagram DM -> WhatsApp).
3. Infers persona and primary signal.
4. Picks template (`T1` to `T6`) and renders final draft.
5. Outputs draft queue with `pending_review` state.

## Scope lock
No auto-follow-up generation. First-touch drafts only.

# First-Touch Outreach Draft Prompt

## How to use
Paste this prompt and provide scored leads (`A` or `B`) plus lead evidence fields.

## Prompt
Task:
Generate first-touch outreach drafts only (no follow-ups).

Entry criteria:
1. priority_bucket in `A` or `B`
2. outreach_status = `not_started`
3. at least one direct channel:
   - valid email, or
   - Instagram DM path, or
   - WhatsApp business contact

Channel priority:
1. email (if valid)
2. instagram_dm
3. whatsapp

Message rules:
1. Mention one real observed signal.
2. Connect to one Trio&Buy value pillar:
   - trial confidence
   - CAC efficiency
   - zero-party feedback data
   - full-size conversion loop
3. One clear CTA.
4. No guaranteed ROI or fake claims.
5. No follow-up text.

Output strict JSON:
```json
{
  "draft_queue": [
    {
      "lead_id": "string",
      "channel_selected": "email|instagram_dm|whatsapp",
      "template_hint": "T1|T2|T3|T4|T5|T6",
      "message_subject": "string|null",
      "message_draft": "string",
      "personalization_reason": "string",
      "review_status": "pending_review",
      "send_status": "not_sent"
    }
  ],
  "skipped_outreach": [
    {
      "lead_id": "string",
      "reason": "not_priority_bucket|outreach_already_started|no_reachable_channel|no_template_match"
    }
  ]
}
```

INPUT_SCORED_LEADS_JSON:
```json
[]
```

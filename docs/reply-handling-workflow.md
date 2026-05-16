# Reply Handling Workflow (v1)

## Purpose
This file defines what happens after a brand replies to first-touch outreach. It ensures every reply is categorized, logged, and routed to the right manual next step without any auto follow-up behavior.

## Goal
Process inbound replies consistently, protect sender reputation, and hand off all real conversations to the founder/team.

## Inputs required
1. `docs/lead-data-schema.md`
2. `docs/outreach-workflow.md`
3. `docs/message-template-bank.md`
4. Outbound message log (`lead_id`, channel, sent timestamp)
5. Inbound reply payload (reply text, channel, timestamp)

## Scope
1. This workflow handles replies to first-touch outreach only.
2. No auto follow-up generation is allowed.
3. Any next outbound message after a reply is manual by founder/team.

## Reply category definitions
1. `positive`
   - Brand shows interest in pilot/call/details.
2. `neutral`
   - Brand asks a question or requests more context but does not commit.
3. `negative`
   - Brand declines without escalation language.
4. `not_relevant`
   - Wrong contact/person/brand fit mismatch.
5. `opt_out`
   - Explicit stop/unsubscribe/block request.
6. `unclear`
   - Reply cannot be reliably classified; requires manual review.

## Classification rules
1. Use strongest explicit intent in the reply.
2. If both interest and opt-out appear, classify as `neutral`.
3. If reply is ambiguous, classify as `unclear`.
4. Save a confidence score (`high`, `medium`, `low`) for auditability.

## Action map (no auto follow-up)
1. `positive`
   - Action: mark as `handoff_required`.
   - Owner: founder/team.
   - Status update: `response_status = positive`, `outreach_status = replied`.
   - Next step: create manual task for call/pilot discussion.
2. `neutral`
   - Action: mark as `manual_reply_required`.
   - Owner: founder/team.
   - Status update: `response_status = neutral`, `outreach_status = replied`.
   - Next step: founder/team sends manual clarifying response.
3. `negative`
   - Action: mark as `closed_no_interest`.
   - Owner: system.
   - Status update: `response_status = negative`, `outreach_status = closed`.
4. `not_relevant`
   - Action: mark as `closed_not_relevant`.
   - Owner: system.
   - Status update: `response_status = negative`, `outreach_status = closed`.
   - Next step: optionally update targeting notes manually.
5. `opt_out`
   - Action: mark as `suppressed`.
   - Owner: system.
   - Status update: `response_status = negative`, `outreach_status = closed`.
   - Mandatory: set `do_not_contact = true` immediately.
6. `unclear`
   - Action: mark as `manual_review_required`.
   - Owner: founder/team.
   - Status update: `outreach_status = replied`.

## Fields to capture for each reply
1. `lead_id`
2. `channel_selected`
3. `reply_text`
4. `reply_received_at`
5. `reply_type` (`positive | neutral | negative | not_relevant | opt_out | unclear`)
6. `classification_confidence` (`high | medium | low`)
7. `action_taken`
8. `action_owner` (`system | founder_team`)
9. `response_status`
10. `outreach_status`
11. `do_not_contact` (`true | false`)
12. `manual_task_id` (optional)
13. `notes` (optional)
14. `updated_at`

## Suppression and safety rules
1. If `reply_type = opt_out`, set `do_not_contact = true` immediately.
2. Never send further outreach when `do_not_contact = true`.
3. Maintain a suppression list keyed by:
   - email
   - instagram_handle
   - whatsapp number
4. Respect channel-specific stop signals (for example "stop", "unsubscribe", "do not message").
5. Do not override suppression without explicit manual approval.

## Routing and manual handoff
1. Route `positive`, `neutral`, and `unclear` replies to founder/team inbox/task board.
2. Include context packet in handoff:
   - brand profile snapshot
   - outbound message sent
   - inbound reply text
   - recommended next manual action
3. Define SLA for manual handling (for example within 24 hours).

## Output tables/files
1. `reply_log`
   - all replies with classification and action fields
2. `manual_handoff_queue`
   - replies needing founder/team action
3. `suppression_list`
   - do-not-contact identities and reason
4. `reply_run_summary`
   - daily counts and category distribution

## Quality checks
1. Every reply has exactly one `reply_type`.
2. Every `reply_type` maps to one valid `action_taken`.
3. Every `opt_out` sets `do_not_contact = true`.
4. No suppressed lead appears in outbound queue again.
5. Manual handoff items include complete context packet.

## Daily metrics to track
1. Total replies received
2. Positive reply count and rate
3. Neutral reply count and rate
4. Negative/not_relevant count and rate
5. Opt-out count and rate
6. Unclear classification count
7. Average manual handoff completion time
8. Suppression list growth

## Completion checklist
1. Replies ingested and matched to `lead_id`.
2. Classification completed with confidence.
3. Action map applied with correct status updates.
4. Suppression updates applied for opt-outs.
5. Manual handoff queue generated.
6. Reply run summary saved.

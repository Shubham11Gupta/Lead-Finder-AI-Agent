# Outreach Workflow (v1)

## Purpose
This file is the messaging playbook. It defines how leads are converted into personalized outreach drafts, how those drafts are reviewed, and when messages are allowed to be sent.

## Goal of this workflow
Send relevant, respectful, and high-quality outreach to Priority A/B leads with clear personalization and safe communication practices.

## Inputs required
1. `docs/targeting-spec.md`
2. `docs/lead-data-schema.md`
3. `docs/lead-scoring-spec.md`
4. `docs/scoring-workflow.md`
5. `scored_leads` output

## Outreach entry criteria
A lead can enter outreach only if:
1. `priority_bucket` is `A` or `B`
2. `outreach_status = not_started`
3. At least one direct channel exists:
   - valid email, or
   - active Instagram DM path, or
   - WhatsApp business contact

## Channel selection logic
1. If valid email exists, choose email as primary channel.
2. If no valid email, use Instagram DM.
3. If no email and no active IG DM, use WhatsApp business contact.
4. Use one primary channel first; do not blast all channels at once.

## Personalization data points to use
Use only verified signals from lead data:
1. Category and product type
2. Recent launch signal
3. Paid ads signal
4. UGC/review depth signal
5. Public review/testimonial request signal
6. Sample/trial feasibility signal
7. Reachability channel context

## Deck-derived value pillars (use these in messaging)
1. Conversion pillar:
   - Low-risk sample trial can improve first-purchase confidence.
2. CAC pillar:
   - Better-qualified trial users can reduce wasted paid acquisition spend.
3. Data pillar:
   - Verified feedback flow produces zero-party consumer signals brands can act on.
4. Retention pillar:
   - Rewards-led loop (Trio Coins) can increase full-size conversion intent.

## Message generation rules
1. Mention one specific observed signal.
2. Explain one deck-aligned value pillar linked to that signal.
3. Keep message short and clear.
4. Use one simple CTA.
5. Do not use fake personalization.
6. Do not make unverifiable claims or guaranteed outcomes.
7. Do not use manipulative urgency.

## Tone and style rules
1. Helpful, businesslike, and respectful.
2. No spammy words, hype, or aggressive pressure.
3. Avoid long paragraphs.
4. Use plain language and clear next step.

## Message structure template
1. Opener:
   - short intro with brand name and one observed signal
2. Relevance:
   - one sentence about their likely challenge
3. Value:
   - one sentence on sample-led acquisition + feedback loop fit
4. CTA:
   - low-friction ask (for example, 15-minute call or pilot interest)
5. Close:
   - sender identity and simple opt-out line when required

## Persona-level angle guidance
1. Founder / Co-founder:
   - Focus on CAC efficiency, conversion lift, and repeat purchase potential.
2. Head of Growth / Performance Marketing:
   - Focus on paid traffic quality, creative feedback loops, and measurable funnel impact.
3. E-commerce Manager / Brand Manager:
   - Focus on launch traction, review depth, and SKU-level demand learning.

## Approved claims and prohibited claims
1. Approved (if relevant evidence exists):
   - "sample-led discovery"
   - "verified consumer feedback"
   - "zero-party insights"
   - "full-size conversion optimization"
2. Prohibited:
   - guaranteed ROI claims
   - guaranteed conversion percentages
   - false partnership references
   - fabricated performance benchmarks

## Channel-specific draft guidance

### Email
1. Subject line: 5 to 9 words, specific and non-clickbait.
2. Body length: 80 to 160 words.
3. Include identity and clear reply CTA.
4. Include opt-out/unsubscribe instruction where applicable.

### Instagram DM
1. Body length: 40 to 100 words.
2. Keep CTA very light.
3. Avoid links in first message unless necessary.
4. End with a clear first-response CTA and wait for reply.

### WhatsApp
1. Keep first message concise and friendly.
2. Confirm recipient relevance quickly.
3. Use one CTA only.
4. Respect local messaging consent expectations.

## Compliance and safety rules
1. Use only publicly available business-relevant data.
2. Respect platform terms and anti-spam laws in target region.
3. Always identify sender/company clearly.
4. Provide simple opt-out path when channel supports it.
5. Never misrepresent identity, outcomes, or partnerships.
6. Do not message again after explicit opt-out.

## Human review gate
Drafts must pass review before send:
1. Signal used is real and evidence-backed.
2. Message is relevant to category and stage.
3. No policy/safety violations.
4. Grammar and clarity are acceptable.
5. CTA is clear and low-friction.

## Outreach statuses
1. `not_started`
2. `draft_ready`
3. `pending_review`
4. `approved`
5. `sent`
6. `replied`
7. `closed`

## Manual handoff policy
1. This project supports first-touch outreach only.
2. Follow-up decisions are handled manually by the founder/team.
3. The system should not auto-generate or auto-send follow-ups.

## A/B test plan
Test one variable at a time:
1. Subject line style:
   - Variant A: signal-driven subject
   - Variant B: outcome-driven subject
2. CTA style:
   - Variant A: "open to a 15-minute pilot call?"
   - Variant B: "want a one-SKU Trio Box pilot outline?"
3. Track by channel and bucket (`A` vs `B`).

## Output fields to save
1. `lead_id`
2. `channel_selected`
3. `message_subject` (for email)
4. `message_draft`
5. `personalization_reason`
6. `review_status`
7. `send_status`
8. `sent_at`
9. `last_outreach_at`
10. `response_status`

## Required quality checks
1. Every sent message references at least one verified signal.
2. Every message has one clear CTA.
3. No message is sent without review approval.
4. No lead receives duplicate same-day outreach on multiple channels.
5. Outreach statuses are updated after each action.

## Daily outreach metrics
1. Drafts created
2. Draft approval rate
3. Messages sent by channel
4. Reply rate by channel
5. Positive reply rate by channel
6. Opt-out rate
7. Top-performing personalization signals

## Completion checklist for each outreach run
1. Eligible leads selected from scoring output.
2. Drafts generated with verified personalization.
3. Human review completed.
4. Approved messages sent on chosen primary channel.
5. Statuses and timestamps updated.
6. Metrics summary saved.

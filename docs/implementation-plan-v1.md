# Implementation Plan (v1)

## Purpose
This file is your build roadmap. It converts architecture into a coding sequence so you can implement the system step by step without confusion.

## Scope lock
1. First-touch outreach only.
2. No automated follow-up generation or scheduling.
3. Manual founder/team handoff after inbound replies.

## V1 Priority Focus
1. Internet-based lead discovery is the primary path (API/connectors first).
2. File-based connectors are fallback/dev tooling, not the final acquisition path.
3. Email sending capability is in-scope for v1 after scoring + draft + approval flow.

## Build strategy
1. Build smallest working pipeline first.
2. Add quality/safety checks early.
3. Ship phase-by-phase with testable milestones.

## Recommended project structure (example)
1. `src/config/`
2. `src/schema/`
3. `src/connectors/`
4. `src/collection/`
5. `src/scoring/`
6. `src/outreach/`
7. `src/reply/`
8. `src/suppression/`
9. `src/analytics/`
10. `src/shared/`
11. `tests/`
12. `data/` (local dev only)

## Phase 1 - Foundation and schema validation
### Goal
Set up project, base configs, and strict lead schema validation.

### Build tasks
1. Create project folders and baseline config.
2. Implement lead schema types/models from `lead-data-schema.md`.
3. Add input validation functions for required fields and enums.
4. Implement basic logging and error format.

### Inputs
1. `docs/lead-data-schema.md`
2. `docs/system-architecture-v1.md`

### Outputs
1. Schema validator module.
2. Sample valid/invalid lead fixtures.

### Done criteria
1. Valid lead payload passes validation.
2. Invalid payload returns clear field-level errors.
3. Enum fields reject unknown values unless explicitly allowed.

### Test checklist
1. Missing required field test.
2. Invalid enum value test.
3. Array field type test.
4. Timestamp format test.

## Phase 2 - Collection pipeline (discover -> qualify)
### Goal
Ingest candidate leads, enrich fields, deduplicate, and produce qualified queue.

### Build tasks
1. Implement connector interfaces (Instagram/Ad Library/Search placeholders first).
2. Build collection normalizer to map raw data into schema.
3. Add dedup logic by handle/url/name+region.
4. Add qualification gate checks from `collection-workflow.md`.
5. Save outputs to:
   - `raw_discovered_leads`
   - `qualified_leads_ready_for_scoring`
   - `skipped_leads`

### Inputs
1. `docs/source-discovery-plan.md`
2. `docs/collection-workflow.md`
3. `docs/lead-data-schema.md`

### Outputs
1. Collection run artifact with counts and skip reasons.

### Done criteria
1. One run can process a batch end-to-end.
2. Duplicate candidates merge correctly.
3. Every qualified lead has at least one reachable channel and evidence URL.

### Test checklist
1. Duplicate merge test.
2. Qualification pass/fail test.
3. Unknown-field handling test.
4. Evidence URL presence test.

## Phase 3 - Scoring engine
### Goal
Apply deterministic scoring and produce priority buckets with reasons.

### Build tasks
1. Implement hard-skip checks.
2. Implement dimension scoring with section caps.
3. Implement penalties and final score formula.
4. Assign bucket (`A`, `B`, `skip`) based on spec.
5. Persist score breakdown and reason logs.

### Inputs
1. `qualified_leads_ready_for_scoring`
2. `docs/lead-scoring-spec.md`
3. `docs/scoring-workflow.md`

### Outputs
1. `scored_leads`
2. `skipped_scoring`
3. `scoring_run_summary`

### Done criteria
1. Score always in 0 to 100.
2. Hard-skip leads never enter scored table.
3. Every scored lead has section-wise score + final reason log.

### Test checklist
1. Hard-skip enforcement test.
2. Score cap test per section.
3. Penalty math test.
4. Bucket threshold boundary tests.

## Phase 4 - Outreach draft engine + human review gate
### Goal
Generate first-touch personalized drafts and enforce manual approval before send.

### Build tasks
1. Implement template selection by persona + channel + signal.
2. Inject verified personalization fields into templates.
3. Add approved/prohibited claim checks.
4. Add review state machine:
   - `draft_ready` -> `pending_review` -> `approved/rejected`
5. Store draft metadata for audit.

### Inputs
1. `scored_leads` (`A` and `B`)
2. `docs/outreach-workflow.md`
3. `docs/message-template-bank.md`

### Outputs
1. Draft queue with review statuses.

### Done criteria
1. Drafts generated only for `A/B` leads.
2. Drafts include one verified signal and one CTA.
3. No draft can be sent without approval.

### Test checklist
1. Template matching test.
2. Placeholder fill test.
3. Prohibited claim detection test.
4. Review-gate blocking test.

## Phase 5 - Sender + reply handling + suppression
### Goal
Send approved first-touch messages, classify replies, and enforce do-not-contact rules.

### Build tasks
1. Implement channel sender adapters (email/IG DM/WhatsApp abstraction).
2. Add idempotent send protection.
3. Implement reply intake parser.
4. Implement reply classification and action mapping.
5. Implement suppression list and pre-send suppression check.
6. Implement manual handoff queue creation for positive/neutral/unclear replies.

### Inputs
1. `approved` outreach messages
2. `docs/reply-handling-workflow.md`

### Outputs
1. `outreach_messages` log
2. `reply_log`
3. `manual_handoff_queue`
4. `suppression_list`

### Done criteria
1. Sent events are logged with timestamps.
2. Every reply gets one category and action.
3. `opt_out` always sets `do_not_contact = true`.
4. Suppressed contacts are blocked from future sends.

### Test checklist
1. Send idempotency test.
2. Reply classification mapping test.
3. Opt-out suppression test.
4. Pre-send suppression block test.

## Phase 6 - Analytics and reporting
### Goal
Generate daily and weekly metrics for decision-making.

### Build tasks
1. Build metric aggregators from all run artifacts.
2. Compute funnel conversion metrics and drop-offs.
3. Compute quality metrics and compliance metrics.
4. Build template/channel performance views.
5. Output daily snapshot and weekly report files.

### Inputs
1. `docs/analytics-metrics-framework.md`
2. Collection, scoring, outreach, and reply logs

### Outputs
1. `daily_metrics_snapshot`
2. `weekly_metrics_report`
3. Channel/template performance reports

### Done criteria
1. All core metrics are generated with formulas.
2. Weekly report highlights bottlenecks and top actions.
3. First-touch constraints are monitored (`auto_followup_count = 0`).

### Test checklist
1. Formula correctness test.
2. Missing data resilience test.
3. Breakdown grouping test.
4. First-touch constraint validation test.

## Milestone checkpoints
1. `M1`: First valid lead stored in `lead_master`.
2. `M2`: First qualified lead scored with full breakdown.
3. `M3`: First outreach draft created and approved.
4. `M4`: First first-touch message sent and logged.
5. `M5`: First reply classified and routed.
6. `M6`: First weekly analytics report generated.

## Risks and fallback plan
1. Data sparsity from social-first brands:
   - fallback: allow `unknown` for non-critical fields, require evidence URLs.
2. Platform access limits or policy changes:
   - fallback: modular connectors + source switching.
3. Low message relevance:
   - fallback: tighten template selection and signal validation.
4. High opt-out rate:
   - fallback: reduce send volume, adjust copy, stricter qualification gate.
5. Reply misclassification:
   - fallback: `unclear` route to manual review.

## Operational cadence
1. Daily:
   - run collection, scoring, draft generation, reply classification.
2. Weekly:
   - review analytics report and choose top 3 improvements.
3. Monthly:
   - refresh template bank and scoring thresholds.

## Definition of done (project v1)
1. End-to-end flow works for at least one real lead from discovery to reply logging.
2. No auto-follow-up behavior exists in system.
3. Suppression and opt-out enforcement works reliably.
4. Metrics are produced daily and reviewed weekly.
5. Manual handoff queue is active for real replies.

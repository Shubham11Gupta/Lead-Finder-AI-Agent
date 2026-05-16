# Analytics Metrics Framework (v1)

## Purpose
This file is the performance report card for the lead engine. It defines what to measure at each stage so the team can spot bottlenecks, improve quality, and increase conversion from discovery to positive reply.

## Goal of analytics
1. Measure end-to-end funnel health.
2. Identify where leads drop off.
3. Compare channel and template performance.
4. Improve first-touch outreach quality over time.

## Scope
1. First-touch outreach only.
2. No automated follow-up metrics are included.

## Funnel stages to measure
1. `discovered`
2. `qualified`
3. `scored_a`
4. `scored_b`
5. `draft_ready`
6. `approved`
7. `sent`
8. `replied`
9. `positive_reply`
10. `neutral_reply`
11. `negative_reply`
12. `opt_out`

## Core metrics and formulas
1. `qualification_rate = qualified / discovered`
2. `priority_a_rate = scored_a / qualified`
3. `priority_b_rate = scored_b / qualified`
4. `draft_rate = draft_ready / (scored_a + scored_b)`
5. `approval_rate = approved / draft_ready`
6. `send_rate = sent / approved`
7. `reply_rate = replied / sent`
8. `positive_reply_rate = positive_reply / sent`
9. `neutral_reply_rate = neutral_reply / sent`
10. `negative_reply_rate = negative_reply / sent`
11. `opt_out_rate = opt_out / sent`
12. `a_to_positive_rate = positive_reply / scored_a`

## Breakdown views
Track all key metrics by:
1. `channel_selected` (`email`, `instagram_dm`, `whatsapp`)
2. `persona` (`founder`, `growth`, `brand_manager`)
3. `category` (beauty, nutrition, snacks, pet care, health care)
4. `source_platform` (instagram, ad_library, places, google_search, website)
5. `priority_bucket` (`A`, `B`)
6. `brand_presence_type` (`website_brand`, `social_first_unregistered`)

## Stage drop-off analysis
Calculate and monitor:
1. `discover_to_qualified_drop = 1 - qualification_rate`
2. `qualified_to_sent_drop = 1 - (sent / qualified)`
3. `sent_to_replied_drop = 1 - reply_rate`
4. `replied_to_positive_drop = 1 - (positive_reply / replied)`

## Weekly review format
1. Funnel summary:
   - discovered -> qualified -> sent -> replied -> positive
2. Top wins:
   - best-performing channel
   - best-performing persona angle
   - best-performing template IDs
3. Top bottlenecks:
   - biggest drop-off stage
   - lowest-performing channel
4. Top skip reasons from collection/scoring
5. Top opt-out reasons
6. Action plan for next week (max 3 actions)

## Data quality metrics
1. `missing_required_field_rate = leads_with_missing_required / total_leads`
2. `unknown_field_rate = total_unknown_fields / total_fields_checked`
3. `evidence_url_coverage = leads_with_source_urls / total_leads`
4. `valid_contact_channel_rate = leads_with_at_least_one_channel / total_leads`
5. `dedup_merge_rate = merged_duplicates / discovered`

## Message quality metrics
1. `personalization_coverage = messages_with_verified_signal / sent`
2. `single_cta_compliance_rate = messages_with_one_cta / sent`
3. `policy_violation_rate = rejected_for_policy / draft_ready`
4. `manual_edit_rate = manually_edited_drafts / draft_ready`

## A/B test tracking
For each template variant, store:
1. `template_id`
2. `variant_id`
3. `channel_selected`
4. `persona`
5. `sent_count`
6. `replied_count`
7. `positive_reply_count`
8. `opt_out_count`
9. `reply_rate = replied_count / sent_count`
10. `positive_rate = positive_reply_count / sent_count`
11. `opt_out_rate = opt_out_count / sent_count`

## First-touch only constraint metrics
1. `auto_followup_count` must always be `0`.
2. `messages_sent_after_opt_out` must always be `0`.
3. `manual_handoff_rate = replies_routed_to_founder_team / replied`.

## Operational KPIs
1. `time_to_draft` (avg time from scored to draft_ready)
2. `time_to_approval` (avg time from draft_ready to approved)
3. `time_to_send` (avg time from approved to sent)
4. `time_to_reply_classification` (avg time from reply received to reply_type assigned)

## Targets (initial v1 benchmarks, editable)
1. `qualification_rate >= 35%`
2. `reply_rate >= 8%`
3. `positive_reply_rate >= 3%`
4. `opt_out_rate <= 2%`
5. `evidence_url_coverage >= 95%`
6. `auto_followup_count = 0`

## Output artifacts
1. `daily_metrics_snapshot`
2. `weekly_metrics_report`
3. `channel_performance_report`
4. `template_performance_report`
5. `data_quality_report`

## Dashboard sections (if implemented later)
1. Funnel overview
2. Channel comparison
3. Persona and category performance
4. Template A/B leaderboard
5. Quality and compliance panel
6. Opt-out and suppression panel

## Completion checklist
1. All formulas are implemented consistently.
2. Daily snapshots are generated.
3. Weekly review report is produced.
4. First-touch constraints are validated (`auto_followup_count = 0`).
5. Next-week action items are documented.

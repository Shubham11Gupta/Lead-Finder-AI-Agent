# Scoring Workflow (v1)

## Purpose
This file is the scoring playbook. It explains how qualified leads are converted into numeric scores and priority buckets (`A`, `B`, `skip`) in a consistent way.

## Goal of this workflow
Score each qualified lead using the same rules every time, record a full score breakdown, and produce a prioritized outreach queue.

## Inputs required
1. `docs/lead-scoring-spec.md`
2. `docs/lead-data-schema.md`
3. `docs/collection-workflow.md`
4. `qualified_leads_ready_for_scoring` output from collection step

## Scoring run setup
1. Create a scoring run ID: `score_run_YYYYMMDD_01`.
2. Freeze rule version:
   - scoring spec version
   - schema version
3. Load all qualified leads for this run.

## Scoring order (for each lead)
1. Validate required scoring fields are present.
2. Apply hard-skip rules first.
3. Compute dimension scores:
   - `icp_fit_score` (0-40)
   - `need_intent_score` (0-35)
   - `operational_feasibility_score` (0-15)
   - `reachability_score` (0-10)
4. Compute base score:
   - `base_score = icp_fit_score + need_intent_score + operational_feasibility_score + reachability_score`
5. Apply penalties:
   - `penalty_total = sum(all applicable penalties)`
6. Compute final score:
   - `final_score = max(0, min(100, base_score - penalty_total))`
7. Assign priority bucket:
   - `A`, `B`, or `skip`
8. Save score breakdown and reason log.

## Hard-skip rules
1. If no reachable channel exists (no valid email, no active Instagram DM, no WhatsApp), mark as `skip`.
2. If lead matches hard disqualifier from targeting spec, mark as `skip`.
3. Store explicit skip reason code.

## Dimension scoring method

### 1) ICP Fit (max 40)
1. Category match score
2. Stage match score
3. Team size match score
4. Region match score
5. Cap this section at 40

### 2) Need/Intent Signals (max 35)
1. Product/SKU launch recency
2. Public review/testimonial requests
3. New digital presence signal
4. Low UGC/review depth signal
5. Paid ads signal
6. Cap this section at 35

### 3) Operational Feasibility (max 15)
1. Sampling feasibility signal
2. Sample shipping capability signal
3. Margin viability signal
4. Cap this section at 15

### 4) Reachability (max 10)
1. At least one direct reachable channel
2. Social fallback readiness
3. Website contact form status
4. Cap this section at 10

## Penalty application method
1. Apply only penalties defined in `lead-scoring-spec.md`.
2. Multiple penalties can apply to one lead.
3. Record penalty names in `penalties_applied`.
4. Do not allow negative final score (floor at 0).

## Bucket assignment logic
1. If hard-skip triggered, bucket is `skip`.
2. Else if `final_score` is in Priority A range, bucket is `A`.
3. Else if `final_score` is in Priority B range, bucket is `B`.
4. Else bucket is `skip`.

## Reason logging format
Use a compact machine-readable summary for every scored lead:

`final=<n> | icp=<n> need=<n> feas=<n> reach=<n> | penalties=<n> | bucket=<A|B|skip> | reasons=[...]`

Example:

`final=74 | icp=30 need=24 feas=12 reach=8 | penalties=0 | bucket=B | reasons=[new_launch,active_ads,dm_reachable]`

## Output tables/files
1. `scored_leads`
   - all non-hard-skip leads with full score breakdown
2. `skipped_scoring`
   - all hard-skip leads with skip reason codes
3. `scoring_run_summary`
   - run-level counts, score distribution, bucket split

## Required quality checks
1. Every scored lead has all 4 dimension scores + final score + bucket.
2. Every skipped lead has at least one explicit skip reason code.
3. No lead appears in both `scored_leads` and `skipped_scoring`.
4. Final score is always between 0 and 100.
5. Bucket assignment follows scoring spec thresholds exactly.

## Skip reason codes
1. `sampling_not_feasible`
2. `no_reachable_channel`
3. `hard_disqualifier_match`
4. `missing_required_scoring_fields`

## Daily scoring metrics to track
1. Total leads sent to scoring
2. Total leads hard-skipped
3. Total leads scored
4. Average final score
5. Priority A count and rate
6. Priority B count and rate
7. Top penalty reasons
8. Top hard-skip reasons
9. Unknown-field rate in scored leads

## Completion checklist for each scoring run
1. Run ID created and versions frozen.
2. Hard-skip rules applied first.
3. All four dimensions scored with caps.
4. Penalties applied and final score computed.
5. Buckets assigned and reason logs saved.
6. Output tables generated and summary saved.

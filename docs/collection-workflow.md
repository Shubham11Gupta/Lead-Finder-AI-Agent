# Collection Workflow (v1)

## Purpose
This file is your daily operating procedure for lead collection. It tells you exactly what to do, in what order, so leads are collected consistently and are ready for scoring.

## Goal of this workflow
Find early-stage D2C brands, collect evidence-backed lead records, and push only valid leads into the scoring queue.

## Inputs needed before starting
1. `docs/targeting-spec.md`
2. `docs/source-discovery-plan.md`
3. `docs/lead-data-schema.md`
4. `docs/lead-scoring-spec.md`
5. Current lead database or sheet (for dedup check)

## Run frequency and batch size
1. Run this workflow once per day (or at least 3 times per week).
2. Target batch size per run:
   - 30 to 60 discovered leads
   - 15 to 35 qualified leads ready for scoring

## Step-by-step collection flow

### Step 1: Prepare run context
1. Set run date and owner.
2. Set target segment for this run (for example: beauty + nutrition in India).
3. Create a run ID, such as `run_YYYYMMDD_01`.

### Step 2: Discover leads on primary sources
1. Discover on Instagram first using approved keyword/hashtag patterns.
2. Add supporting discovery from:
   - Meta Ad Library
   - Google Places API Text Search
   - Google Search
3. For each candidate, create a draft lead record with:
   - `brand_name`
   - `primary_profile_url`
   - `brand_presence_type`
   - first available contact channel

### Step 3: Enrich each candidate
1. Collect as many required fields from `lead-data-schema.md` as possible.
2. Attach evidence URLs in `source_urls` for each key claim.
3. If a field cannot be confirmed, set it to `unknown` (never guess).

### Step 4: Dedup check
1. Check duplicates in this order:
   - exact `instagram_handle`
   - exact `website_url`
   - normalized `brand_name` + `region`
2. If duplicate is found:
   - merge new evidence into existing lead record
   - update `last_verified_at`
   - do not create a new lead row

### Step 5: Qualification gate (before scoring)
A lead passes only if all are true:
1. Category is consumable D2C (or very close adjacent category).
2. At least one direct reachable channel exists:
   - valid email, or
   - active Instagram DM path, or
   - WhatsApp business contact
3. No hard disqualifier from targeting spec.

If any mandatory gate fails, mark lead as `skip` with a reason code.

### Step 6: Queue leads for scoring
1. Push passed leads to scoring queue.
2. Keep skipped leads in a separate table with explicit skip reasons.
3. Save run summary counts.

## Dedup rules
1. One brand must have one canonical `lead_id`.
2. Use `primary_profile_url` as strongest identity key for social-first brands.
3. If brand name varies across sources, keep one canonical `brand_name` and store alternates in `notes`.

## Unknown-data rules
1. Allowed unknowns:
   - `stage`
   - `team_size`
   - `margin_viability_signal`
   - `launch_recency_days`
   - `sampling_feasibility`
2. Not allowed unknowns (must be known to proceed):
   - `brand_name`
   - `primary_profile_url`
   - `category`
   - at least one reachable channel
3. If mandatory fields are missing, keep in `hold` list for one retry pass, then skip.

## Output tables/files from each run
1. `raw_discovered_leads`:
   - all candidates discovered before dedup and gate
2. `qualified_leads_ready_for_scoring`:
   - all leads that passed gate
3. `skipped_leads`:
   - all leads rejected, with reason codes
4. `run_summary`:
   - totals and quality metrics

## Required quality checks
1. Every qualified lead has at least one reachable channel.
2. Every qualified lead has at least one evidence URL.
3. No duplicate lead IDs in qualified output.
4. Required schema fields are present and type-safe.

## Skip reason codes
1. `non_consumable_category`
2. `no_reachable_channel`
3. `hard_disqualifier_match`
4. `insufficient_evidence`
5. `duplicate_merged`

## Daily metrics to track
1. Total discovered leads
2. Deduped unique leads
3. Qualified leads count
4. Qualification rate (`qualified / discovered`)
5. Top skip reasons
6. Source mix (`instagram`, `ad_library`, `places`, `google_search`, `website`)
7. Unknown-field rate on qualified leads

## Completion checklist for each run
1. Discovery done for target segment.
2. Dedup completed.
3. Qualification gate applied.
4. Qualified leads exported to scoring queue.
5. Skipped leads logged with reason codes.
6. Run summary saved.

# Lead Scoring Spec

## Scoring Dimensions (with weights)
 - ICP Fit (40)
 - Need/Intent Signals (35)
 - Operational Feasibility (15)
 - Reachability (10)

## Sub-rules

### ICP Fit:
 - Exact category match (beauty/nutrition/snacks/pet): +15
 - Stage match: +10
 - Team match: +10
 - Region match: +5

### Need/Intent Signals:
  - Recently launched a product/SKU: +10
  - Publicly asking for reviews/testimonials or community feedback: +8
  - Early digital presence spike/new store listing: +7
  - Low review depth/UGC (trust gap on first purchase): +5
  - Active performance ads (Meta/Google): +5

### Operational Feasibility:
 - Product can be sampled: +5
 - Brand can fulfill sample shipping: +5
 - Sample economics likely viable: +5

### Reachability:
 - At least one direct reachable channel (valid email OR active Instagram DM OR WhatsApp): +5
 - Active social handle for outreach fallback: +3
 - Working website contact form: +2

## Negative Penalties
 - Non-consumable: -40
 - Very low-margin product: -10
 - No sampling feasibility: -15

## Score Buckets + Action
 - 60-100: Priority A (contact first)
 - 30-59: Priority B (contact after A)
 - <30: skip for now

## Scoring Formula
 - base_score = icp_fit + need_intent + operational_feasibility + reachability
 - penalty_total = sum(all applicable penalties)
 - final_score = max(0, min(100, base_score - penalty_total))
 - Hard skip rule 1: if sampling_feasibility = "no", skip
 - Hard skip rule 2: if no reachable channel exists (no valid email, no active instagram_dm, no whatsapp), skip

## Minimum data required to score (website + social-first brands)
 - lead_id
 - brand_name
 - brand_presence_type (website_brand | social_first_unregistered)
 - primary_profile_url
 - website_url (optional)
 - instagram_handle (optional)
 - whatsapp_business_link_or_number (optional)
 - contact_channels_available (array of: email, instagram_dm, whatsapp)
 - founder_or_growth_email (optional)
 - email_validity_signal (valid | invalid | unknown)
 - category
 - stage (pre_revenue | pre_seed | seed | series_a | unknown)
 - registration_status (registered | unregistered | unknown)
 - team_size (optional)
 - region
 - launch_recency_days (optional)
 - ugc_review_depth_signal (high | medium | low | unknown)
 - paid_ads_signal (high | medium | low | unknown)
 - public_review_request_signal (yes | no | unknown)
 - new_digital_presence_signal (yes | no | unknown)
 - sampling_feasibility (yes | no | unknown)
 - shipping_capability (yes | no | unknown)
 - margin_viability_signal (high | medium | low | unknown)
 - social_presence_signal (high | medium | low)
 - contact_form_status (working | missing | unknown)
 - contact_source
 - last_verified_at (optional)

# Source Discovery Plan

## Purpose
This file is the search map for your agent. It tells the agent where to look for startup brands, what data to collect from each platform, and when to skip a lead.

## Schema Version
- version: 1.0
- updated_at: 2026-05-16

## V1 Platforms
1. Instagram (primary discovery for social-first brands)
2. Meta Ad Library (paid ads signal)
3. Google Places API Text Search (verification and enrichment)
4. Google Search (fallback discovery and evidence collection)
5. Brand website/storefront (if available)

## Platform Playbook

### 1) Instagram
- Why this platform:
  - Best source for unregistered and early-stage social-first D2C brands.
- Discovery methods:
  - Search hashtags and keywords like `trial pack`, `sample`, `new launch`, `now shipping`, `D2C India`, `beauty`, `personal care`, `nutrition`, `snacks`, `pet care`, `newly launched`, `health care`.
  - Explore related profiles from seed brands.
- What to extract:
  - `brand_name`
  - `instagram_handle`
  - `primary_profile_url`
  - `whatsapp_business_link_or_number` (if in bio)
  - `category` hints from bio/posts
  - `public_review_request_signal`
  - `new_digital_presence_signal`
  - `social_presence_signal`
  - `sampling_feasibility` hints (`sample`, `trial`, `mini`, `tester`)
- Missing data fallback:
  - If website/email is missing, keep lead if DM/WhatsApp path exists.
  - If sampling feasibility is not available still keep the lead.
- Evidence to store:
  - Profile URL and 1 to 3 relevant post URLs in `source_urls`.

### 2) Meta Ad Library
- Why this platform:
  - Confirms whether brand is actively running paid ads.
- Discovery methods:
  - Search by brand/page name in Ad Library UI.
  - For API access, follow Meta developer flow when available.
- What to extract:
  - `paid_ads_signal`
  - Ad recency and ad count hints
  - Ad creative links for supporting evidence
- Missing data fallback:
  - If no ads are found, set `paid_ads_signal` to `low` or `unknown` (not auto-reject).
- Evidence to store:
  - Ad library search URL and specific ad snapshot URLs.

### 3) Google Places API Text Search
- Why this platform:
  - Good for brand existence checks and local profile enrichment.
- Discovery methods:
  - Query combinations like `brand + city + category`.
  - Use Text Search and optional pagination.
- What to extract:
  - `brand_name`
  - `region`
  - `website_url` (if present)
  - `primary_profile_url` fallback
  - Contact clues and location confidence
- Missing data fallback:
  - If no place match, continue with Instagram-based record.
- Evidence to store:
  - Maps place URL or search URL.

### 4) Google Search
- Why this platform:
  - Fallback discovery when Instagram/Places are incomplete.
- Discovery methods:
  - Query patterns:
    - `"<brand>" + instagram + india`
    - `"<brand>" + trial pack`
    - `"<brand>" + sample`
    - `"<brand>" + whatsapp order`
- What to extract:
  - `website_url`
  - `primary_profile_url`
  - launch/news mentions for `launch_recency_days`
  - directory/listing evidence
- Missing data fallback:
  - Keep lead with unknowns if one direct contact channel exists.
- Evidence to store:
  - Search result URL and clicked source pages.

### 5) Brand Website or Storefront
- Why this platform:
  - Best place for offer clarity and conversion/feasibility checks.
- Discovery methods:
  - Visit official website link from social or search results.
- What to extract:
  - `contact_form_status`
  - `founder_or_growth_email`
  - product pricing clues for `margin_viability_signal`
  - sample/trial program details
  - shipping policy clues for `shipping_capability`
- Missing data fallback:
  - If website is absent, continue with social-first contact channels.
- Evidence to store:
  - Website pages used for scoring (contact, product, shipping, FAQ).

## Field Mapping to Lead Data Schema
- `brand_name`: Instagram, Places, website
- `brand_presence_type`: inferred from available profiles (`website_brand` or `social_first_unregistered`)
- `primary_profile_url`: Instagram first, otherwise website/search listing
- `website_url`: Places, Search, Instagram bio, website
- `instagram_handle`: Instagram
- `whatsapp_business_link_or_number`: Instagram bio, website
- `contact_channels_available`: inferred from email/IG/WhatsApp presence
- `category`: Instagram bio/posts + website/store content
- `stage`: inferred (`pre_revenue | pre_seed | seed | series_a | unknown`)
- `region`: Places, profile bio, website footer
- `launch_recency_days`: launch posts or announcements
- `ugc_review_depth_signal`: website/store reviews and social comments
- `paid_ads_signal`: Meta Ad Library
- `public_review_request_signal`: social posts/captions
- `new_digital_presence_signal`: recent profile/store activity
- `sampling_feasibility`: explicit sample/trial mentions or product format inference
- `shipping_capability`: delivery policy mentions
- `margin_viability_signal`: price point and sample economics approximation
- `contact_source`: first source where lead was discovered
- `source_urls`: all evidence links used
- `last_verified_at`: timestamp of latest verification

## Collection Limits and Safety Rules
1. Respect each platform's terms and policies.
2. Collect only business-relevant public data needed for scoring and outreach.
3. Do not collect sensitive personal data.
4. Keep evidence URLs for auditability.
5. If data confidence is low, mark fields as `unknown` instead of guessing.
6. If no direct contact channel exists, do not send outreach.

## Lead Qualification Gate (Before Scoring)
1. Must be in consumable D2C category or very close adjacent category.
2. Must have at least one reachable channel:
   - valid email, or
   - active Instagram DM path, or
   - WhatsApp business contact.
3. Must not violate hard disqualifiers from targeting spec.
4. If `sampling_feasibility = no`, mark as skip immediately.

## Output Format (from discovery to scoring queue)
1. Create one lead record per brand using fields in `lead-data-schema.md`.
2. Fill unknown values as `unknown` and attach evidence URLs.
3. Push lead to scoring queue only after qualification gate passes.
4. Save `scored_at` and priority bucket after scoring step completes.

## V1 Execution Order
1. Discover on Instagram.
2. Verify paid ads signal via Meta Ad Library.
3. Enrich with Google Places and Google Search.
4. Visit website/storefront if available.
5. Run qualification gate.
6. Send valid leads to scoring.

## Notes
1. This plan intentionally supports website-first and social-first unregistered brands.
2. Start with manual/semi-automated workflows in v1 to validate data quality before full automation.

# Lead Data Schema (v1)

## Purpose
This file defines the exact columns our lead database will use so every part of the system saves and reads data in the same format

## Schema Version
- version: 1.0
- updated_at: 2026-05-16

## Lead Record Fields

### Identity
 - lead_id (string, required)
 - brand_name (string, required)
 - brand_presence_type (enum: website_brand | social_first_unregistered, required)
 - registration_status (enum: registered | unregistered | unknown, required)

### Business Attributes
 - category (string, required)
 - stage (enum:pre_revenue | pre_seed | seed | series_a | unknown, required)
 - region (string, required)
 - team_size (number|string, optional)

### Profiles & Contact
 - primary_profile_url (string,required)
 - website_url (string,optional)
 - instagram_handle (string,optional)
 - whatsapp_business_link_or_number (string,optional)
 - contact_channels_available (array of enum: email, instagram_dm, whatsapp,required)
 - founder_or_growth_email (string,optional)
 - email_validity_signal (enum: valid | invalid | unknown,required)
 - contact_form_status (enum:working | missing | unknown, required)

### Need/Intent Signals
 - launch_recency_days (number|string,optional)
 - ugc_review_depth_signal (enum:high | medium | low | unknown,required)
 - paid_ads_signal (enum:high | medium | low | unknown,required)
 - public_review_request_signal (enum:yes | no | unknown,required)
 - new_digital_presence_signal (enum:yes | no | unknown,required)
 - social_presence_signal (enum:high | medium | low | unknown,required)

### Feasibility
 - sampling_feasibility (enum:yes | no | unknown,required)
 - shipping_capability (enum:yes | no | unknown,required)
 - margin_viability_signal (enum:high | medium | low | unknown,required)

### Scoring Snapshot
 - icp_fit_score (number 0-40, optional)
 - need_intent_score (number 0-35, optional)
 - operational_feasibility_score (number 0-15, optional)
 - reachability_score (number 0-10, optional)
 - penalties_applied (array of strings, optional)
 - final_score (number 0-100, optional)
 - priority_bucket (enum: A | B | skip, optional)
 - scored_at (datetime, optional)

### Outreach Tracking
 - outreach_status (enum: not_started | draft_ready | pending_review | approved | sent | replied | closed, required)
 - last_outreach_at (datetime, optional)
 - response_status (enum: none | positive | neutral | negative, optional)

### Provenance & Audit
 - contact_source (string, required)
 - source_urls (array of strings, optional)
 - notes (string, optional)
 - last_verified_at (datetime, required)
 - created_at (datetime, required)
 - updated_at (datetime, required)
# Message Template Bank (v1)

## Purpose
This file is the reusable outreach message library. It helps the team generate consistent, personalized, and policy-safe drafts for each lead.

## Goal
Convert Priority A/B leads into high-quality first-touch messages with one clear CTA and evidence-backed personalization.

## How templates are selected
1. Select by `persona` first:
   - Founder / Co-founder
   - Head of Growth / Performance Marketing
   - E-commerce Manager / Brand Manager
2. Select by `channel`:
   - email
   - instagram_dm
   - whatsapp
3. Select by strongest verified `signal`:
   - `launch_recency_days`
   - `paid_ads_signal`
   - `ugc_review_depth_signal`
   - `public_review_request_signal`
   - `sampling_feasibility`
4. Use one template per first-touch message.
5. Fill placeholders with verified data only.

## Placeholders
1. `{brand_name}`
2. `{contact_name}`
3. `{category}`
4. `{signal_observed}`
5. `{sku_or_product}`
6. `{sender_name}`
7. `{sender_company}`
8. `{booking_link}`
9. `{whatsapp_number}`

## Approved claims
1. "sample-led discovery"
2. "verified consumer feedback"
3. "zero-party insights"
4. "Trio Box trial flow"
5. "Trio Coins rewards loop"
6. "full-size conversion optimization"

## Avoid claims
1. "guaranteed ROI"
2. "guaranteed conversion lift"
3. "we already partner with [brand]" unless true
4. fake urgency or misleading scarcity

## Template Catalog

### T1 - Founder + Email + New Launch Signal
- template_id: `T1`
- persona: `founder_cofounder`
- channel: `email`
- use_when:
  - `launch_recency_days <= 90`
  - `priority_bucket in [A,B]`
- subject_line:
  - "Launch to Repeat Purchase Loop"
- opening_line:
  - "Hi {contact_name}, noticed {brand_name} recently launched {sku_or_product}."
- value_line:
  - "We help early D2C brands run a closed loop: Trio Box samples -> verified feedback -> Trio Coins -> full-size conversion, while generating zero-party insights."
- cta_line:
  - "Open to a 15-minute pilot discussion for one SKU?"
- fallback_line:
  - "If I reached the wrong person, could you point me to whoever owns growth or launch performance?"

### T2 - Founder + Instagram DM + Paid Ads/CAC Signal
- template_id: `T2`
- persona: `founder_cofounder`
- channel: `instagram_dm`
- use_when:
  - `paid_ads_signal in [high,medium]`
  - `contact_channels_available includes instagram_dm`
- opening_line:
  - "Hey {brand_name} team, saw you actively promoting your products and loved the momentum."
- value_line:
  - "We support D2C founders with a Trio Box trial model that improves first-purchase trust and converts verified trial users into full-size buyers."
- cta_line:
  - "Would you be open to a quick 15-minute pilot chat?"
- fallback_line:
  - "Happy to share a one-SKU pilot outline here if easier."

### T3 - Head of Growth + Email + Low UGC Signal
- template_id: `T3`
- persona: `head_of_growth`
- channel: `email`
- use_when:
  - `ugc_review_depth_signal in [low,unknown]`
  - `priority_bucket in [A,B]`
- subject_line:
  - "Improve UGC Quality for {brand_name}"
- opening_line:
  - "Hi {contact_name}, I noticed a strong product push at {brand_name} and an opportunity to deepen verified review volume."
- value_line:
  - "Our flow captures structured, verified trial feedback and links it to conversion behavior, giving your growth team actionable zero-party signals."
- cta_line:
  - "Would a one-SKU pilot brief be useful this week?"
- fallback_line:
  - "If helpful, I can send a short example of how we map feedback signals to campaign decisions."

### T4 - Head of Growth + Instagram DM + Active Ads Signal
- template_id: `T4`
- persona: `head_of_growth`
- channel: `instagram_dm`
- use_when:
  - `paid_ads_signal in [high,medium]`
  - `contact_channels_available includes instagram_dm`
- opening_line:
  - "Hi, noticed {brand_name} is running active campaigns and scaling awareness."
- value_line:
  - "We run a sample-led conversion loop so paid traffic can be supported by verified trial feedback and stronger first-order confidence."
- cta_line:
  - "Open to a quick chat on a one-SKU test?"
- fallback_line:
  - "Can share a concise pilot flow directly in DM if preferred."

### T5 - E-commerce/Brand Manager + Email + Review Depth Gap
- template_id: `T5`
- persona: `ecommerce_or_brand_manager`
- channel: `email`
- use_when:
  - `ugc_review_depth_signal in [low,unknown]`
  - `public_review_request_signal in [yes,unknown]`
- subject_line:
  - "Stronger Product Feedback Loop for {brand_name}"
- opening_line:
  - "Hi {contact_name}, saw {brand_name} in {category} and noticed strong potential to improve product-level review depth."
- value_line:
  - "Trio Box trials bring in verified product feedback and create a rewards-led path to full-size purchase."
- cta_line:
  - "Would you like a one-page pilot plan for your top SKU?"
- fallback_line:
  - "If relevant, I can tailor the plan to your current launch calendar."

### T6 - E-commerce/Brand Manager + WhatsApp + Sampling Feasibility Signal
- template_id: `T6`
- persona: `ecommerce_or_brand_manager`
- channel: `whatsapp`
- use_when:
  - `sampling_feasibility in [yes,unknown]`
  - `contact_channels_available includes whatsapp`
- opening_line:
  - "Hi {contact_name}, this is {sender_name} from {sender_company}. We help D2C brands run sample-led discovery."
- value_line:
  - "For brands like {brand_name}, Trio Box trials + verified feedback + Trio Coins can improve full-size conversion while generating zero-party insights."
- cta_line:
  - "Can we schedule a 15-minute call to discuss a one-SKU pilot?"
- fallback_line:
  - "If easier, I can send a short pilot summary on WhatsApp first."

## Manual Follow-up Note
1. This template bank is for first-touch outreach only.
2. Follow-up messages are handled manually by the founder/team.

## CTA Variants
1. "Open to a 15-minute pilot discussion?"
2. "Would a one-SKU pilot brief be useful?"
3. "Want a one-page pilot outline for your top SKU?"
4. "Should I send a concise pilot summary first?"

## Quality Checklist
1. Message references at least one verified signal.
2. Message contains exactly one clear CTA.
3. No guaranteed outcomes or fabricated claims.
4. Channel and persona match template `use_when`.
5. If uncertain, use fallback line instead of guessing.

## Notes
1. This is v1 and should be revised monthly using reply-rate data.
2. Keep language simple for social-first brands and concise for founders.

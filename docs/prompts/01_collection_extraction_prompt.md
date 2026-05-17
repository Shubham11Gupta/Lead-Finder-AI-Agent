# Collection + Extraction Prompt

## How to use
Paste this prompt, then paste raw evidence under `INPUT_EVIDENCE`:
1. search snippets
2. Instagram profile notes
3. website/about/contact excerpts
4. ad library notes

## Prompt
Task:
Extract structured lead records from INPUT_EVIDENCE for India D2C consumable brands.

Rules:
1. Use evidence only. If unknown, output `unknown`.
2. Keep one lead per brand.
3. Prefer social-first leads if website is missing.
4. Do not invent emails or phone numbers.
5. Include source links in `source_urls`.
6. First-touch scope only.

Return strict JSON with this schema:
```json
{
  "leads": [
    {
      "brand_name": "string",
      "primary_profile_url": "string",
      "instagram_handle": "string|unknown",
      "website_url": "string|unknown",
      "whatsapp_business_link_or_number": "string|unknown",
      "contact_channels_available": ["email|instagram_dm|whatsapp"],
      "category": "string|unknown",
      "stage": "pre_revenue|pre_seed|seed|series_a|unknown",
      "region": "India|unknown",
      "launch_recency_days": "number|unknown",
      "ugc_review_depth_signal": "high|medium|low|unknown",
      "paid_ads_signal": "high|medium|low|unknown",
      "public_review_request_signal": "yes|no|unknown",
      "new_digital_presence_signal": "yes|no|unknown",
      "sampling_feasibility": "yes|no|unknown",
      "shipping_capability": "yes|no|unknown",
      "margin_viability_signal": "high|medium|low|unknown",
      "brand_presence_type": "website_brand|social_first_unregistered",
      "registration_status": "registered|unregistered|unknown",
      "contact_source": "string",
      "source_urls": ["string"],
      "evidence_notes": "string"
    }
  ],
  "uncertainties": ["string"],
  "discarded_candidates": [
    {
      "name_or_url": "string",
      "reason": "string"
    }
  ]
}
```

INPUT_EVIDENCE:
```text
<PASTE RAW EVIDENCE HERE>
```

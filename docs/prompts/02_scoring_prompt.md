# Lead Scoring Prompt

## How to use
Paste this prompt and provide one or more lead JSON objects from collection output.

## Prompt
Task:
Score each lead from 0 to 100 and assign bucket `A`, `B`, or `skip`.

Scoring model:
1. ICP Fit (40 max)
   - category match: +15
   - stage match (pre_revenue/pre_seed/seed/series_a): +10
   - team size match (1-60 if known): +10
   - region match (India): +5
2. Need/Intent (35 max)
   - launch <= 90 days: +10
   - public feedback request: +8
   - new digital presence: +7
   - low UGC depth: +5
   - active paid ads (high/medium): +5
3. Operational Feasibility (15 max)
   - sampling feasibility yes: +5
   - shipping capability yes: +5
   - margin viability high/medium: +5 or +3
4. Reachability (10 max)
   - at least one direct reachable channel: +5
   - social fallback present: +3
   - working contact form: +2

Penalties:
1. non-consumable: -40
2. very low margin: -10
3. no sampling feasibility: -15

Hard skip:
1. sampling_feasibility = no
2. no reachable channel
3. missing required scoring fields

Formula:
1. base = icp_fit + need_intent + operational_feasibility + reachability
2. final = max(0, min(100, base - penalty_total))
3. bucket:
   - 60-100 => A
   - 30-59 => B
   - <30 => skip

Return strict JSON:
```json
{
  "scored_leads": [
    {
      "lead_id": "string",
      "icp_fit_score": 0,
      "need_intent_score": 0,
      "operational_feasibility_score": 0,
      "reachability_score": 0,
      "penalties_applied": ["string"],
      "final_score": 0,
      "priority_bucket": "A|B|skip",
      "score_reason_log": "string",
      "reason_tags": ["string"]
    }
  ],
  "skipped_scoring": [
    {
      "lead_id": "string",
      "reason": "sampling_not_feasible|no_reachable_channel|missing_required_scoring_fields|hard_disqualifier_match",
      "missing_fields": ["string"]
    }
  ],
  "summary": {
    "input_count": 0,
    "scored_count": 0,
    "hard_skipped_count": 0
  }
}
```

INPUT_LEADS_JSON:
```json
[]
```

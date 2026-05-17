# Reply Classification Prompt

## How to use
Paste this prompt with inbound reply text and lead context.

## Prompt
Task:
Classify each inbound reply and map it to manual action. No auto-follow-up generation.

Reply types:
1. `positive`
2. `neutral`
3. `negative`
4. `not_relevant`
5. `opt_out`
6. `unclear`

Rules:
1. If reply includes stop/unsubscribe intent, classify `opt_out`.
2. If ambiguous, classify `unclear`.
3. Output one type only per reply.

Action map:
1. positive -> `handoff_required`
2. neutral -> `manual_reply_required`
3. negative -> `closed_no_interest`
4. not_relevant -> `closed_not_relevant`
5. opt_out -> `suppressed` and `do_not_contact=true`
6. unclear -> `manual_review_required`

Return strict JSON:
```json
{
  "reply_results": [
    {
      "lead_id": "string",
      "reply_type": "positive|neutral|negative|not_relevant|opt_out|unclear",
      "classification_confidence": "high|medium|low",
      "action_taken": "handoff_required|manual_reply_required|closed_no_interest|closed_not_relevant|suppressed|manual_review_required",
      "do_not_contact": true,
      "notes": "string"
    }
  ]
}
```

INPUT_REPLIES_JSON:
```json
[]
```

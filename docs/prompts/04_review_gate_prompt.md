# Review Gate Prompt (Manual Approval)

## How to use
Paste this prompt with one draft message and lead evidence.

## Prompt
Task:
Review a first-touch outreach draft and return `approve` or `reject` with reasons and corrected copy.

Checklist:
1. Uses a real signal from evidence.
2. Message is relevant to category/stage.
3. One clear CTA.
4. No fake claims, no guaranteed outcomes.
5. Tone is concise and respectful.
6. No follow-up mechanism included.

Return strict JSON:
```json
{
  "decision": "approve|reject",
  "issues": [
    {
      "type": "relevance|policy|clarity|tone|cta",
      "detail": "string"
    }
  ],
  "revised_draft": {
    "message_subject": "string|null",
    "message_draft": "string"
  },
  "review_notes": "string"
}
```

INPUT_DRAFT_JSON:
```json
{}
```

INPUT_EVIDENCE_JSON:
```json
{}
```

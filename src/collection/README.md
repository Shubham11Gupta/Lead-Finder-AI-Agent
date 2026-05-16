# Collection Module (Step 16)

Phase 2 starter pipeline:
1. Discover candidates through connectors.
2. Normalize raw payloads into lead-shaped records.
3. Deduplicate records.
4. Apply qualification gate.
5. Validate qualified records against schema.

## Main entrypoint
`CollectionPipeline.run(...)` in `pipeline.py`

## Current scope
1. Deterministic rule-based flow.
2. Mock connector support for local testing.
3. Instagram file connector support (`CSV`, `JSON`, `JSONL`) for manual discovery ingestion.
4. Run summary with skip reason counts.

# Schema Module (Step 14)

This module validates lead payloads against `docs/lead-data-schema.md`.

## Public API
1. `validate_lead_record(record)`:
   - returns `ValidationResult` with `is_valid`, `issues`, and `normalized`.
2. `validate_lead_or_raise(record)`:
   - raises `SchemaValidationError` when payload is invalid.

## What is validated
1. Required fields
2. Enum values
3. Array/list field shapes
4. Number ranges for score fields
5. ISO datetime fields
6. Basic string quality (non-empty where provided)

## Next step
Use fixtures under `tests/fixtures/` to implement and run Step 15 tests.

# Source Modules (Step 13 Scaffold)

This folder contains the implementation modules for the lead engine.

## Current status
Step 13 (foundation scaffold) is complete: base folders are created and ready for coding.

## Module map
1. `config/` - environment and runtime configuration
2. `schema/` - lead schema models and validators
3. `connectors/` - source platform adapters
4. `collection/` - discovery, enrichment, dedup, qualification
5. `scoring/` - scoring and prioritization logic
6. `outreach/` - template selection and draft generation
7. `reply/` - inbound reply intake and classification
8. `suppression/` - do-not-contact checks and list management
9. `analytics/` - metrics calculations and reporting outputs
10. `shared/` - common utilities (logging, errors, helpers)

## Next step
Implement Step 14: schema models + validator based on `docs/lead-data-schema.md`.

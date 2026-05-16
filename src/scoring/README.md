# Scoring Module (Step 18)

This module converts qualified leads into scored priorities (`A`, `B`, `skip`) using deterministic rules.

## Main entrypoint
`ScoringEngine.run(leads, run_context=...)`

## What it does
1. Applies hard-skip checks.
2. Computes section scores:
   - `icp_fit_score` (0-40)
   - `need_intent_score` (0-35)
   - `operational_feasibility_score` (0-15)
   - `reachability_score` (0-10)
3. Applies penalties and computes final score.
4. Assigns bucket and writes reason logs.
5. Returns scoring run summary metrics.

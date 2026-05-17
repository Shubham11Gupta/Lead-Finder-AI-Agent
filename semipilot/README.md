# Semipilot (Prompt-Driven Agent)

This folder automates the same workflow you were doing manually with prompt files.

## What It Does
1. Loads prompt pack from `docs/prompts`.
2. Runs stages in order with an LLM:
   - system setup
   - collection extraction
   - scoring
   - outreach drafting
   - review gate
   - optional reply classification
3. Saves each stage output to `semipilot/runs/<run_id>/`.

## Setup
1. Copy config:
```powershell
Copy-Item semipilot\config.example.json semipilot\config.json
```
2. Fill:
   - `openai_api_key`
   - `sender_name`
   - `sender_company`
3. Add your raw evidence file at `semipilot/input/raw_evidence.txt`.

## Run
```powershell
python -m semipilot.src.main --config semipilot/config.json
```

## Input Notes
1. `raw_evidence.txt` can include search snippets, profile notes, and website excerpts.
2. Optional `replies.json` is used only if `run_reply_classification=true`.


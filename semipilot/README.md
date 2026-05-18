# Semipilot (Prompt-Driven Agent)

This folder automates the same workflow you were doing manually with prompt files, plus web search and Gmail draft creation.

## What It Does
1. Loads prompt pack from `docs/prompts`.
2. Collects lead evidence from web search.
3. Runs stages in order with an LLM:
   - system setup
   - collection extraction
   - scoring
   - outreach drafting
   - review gate
   - optional reply classification
4. Creates Gmail drafts (not sent) for approved outreach messages.
5. Saves each stage output to `semipilot/runs/<run_id>/`.

## Setup
1. Copy config:
```powershell
Copy-Item semipilot\config.example.json semipilot\config.json
```
2. Fill:
   - `openai_api_key`
   - `sender_name`
   - `sender_company`
   - `search` block
   - `gmail_drafts` block

## Required External Setup
1. Google Programmable Search Engine:
   - create/search engine and copy `google_cse_id` (`cx`)
   - create Google API key with Custom Search JSON API enabled
2. Gmail API OAuth:
   - create OAuth client in Google Cloud
   - generate refresh token with scope `https://www.googleapis.com/auth/gmail.compose`
   - fill `oauth_client_id`, `oauth_client_secret`, and `oauth_refresh_token`

## Run
```powershell
python -m semipilot.src.main --config semipilot/config.json
```

## Input Notes
1. If `search.provider=manual_file`, `raw_evidence.txt` is used as input.
2. If `search.provider=google_cse` or `serper`, evidence is collected automatically.
3. Optional `replies.json` is used only if `run_reply_classification=true`.

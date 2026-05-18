# Config

This folder stores runtime configuration templates.

## Usage
1. Copy `app.config.example.json` to `app.config.json`.
2. Fill Serper + delivery credentials.
3. Run `python run_agent.py --config src/config/app.config.json`.

## Notes
1. Keep real secrets out of git.
2. Recommended v1 mode: `delivery.mode = "gmail_draft"` with `gmail_drafts.enabled = true`.
3. `delivery.mode = "smtp_send"` requires valid SMTP credentials.
4. `delivery.mode = "none"` builds queue artifacts without dispatching.

# Config

This folder stores runtime configuration templates.

## Usage
1. Copy `app.config.example.json` to `app.config.json`.
2. Fill API and SMTP credentials.
3. Run `python run_agent.py --config src/config/app.config.json`.

## Notes
1. Keep real secrets out of git.
2. `send.enabled=false` keeps the run in safe draft mode.
3. Set `send.enabled=true` only after SMTP test succeeds.

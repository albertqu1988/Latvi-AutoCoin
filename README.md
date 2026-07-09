# Latvi Auto Coin 🪙

Automated coin claiming bot for **[dash.latvi.space](https://dash.latvi.space)**.

Runs daily via GitHub Actions to:
1. **Claim the daily reward** (+5 Credits, no proxy needed)
2. **Farm linkvertise shortlink coins** (requires a proxy to keep a consistent IP)

## How it works

| Script | Purpose |
|--------|---------|
| `latvi_coins.py` | Core logic: login → daily reward → linkvertise coin farming |
| `latvi_screenshot.py` | Takes a dashboard screenshot and sends it to Telegram (optional) |

The workflow (` .github/workflows/latvi.yml`) runs on:
- **Schedule**: `7 0,12 * * *` (00:07 & 12:07 UTC, twice daily)
- **Manual**: `workflow_dispatch` (Run workflow button)

## Secrets (required)

Set these in **Settings → Secrets and variables → Actions**:

| Secret | Required | Description |
|--------|----------|-------------|
| `LATVI_EMAIL` | ✅ | Login email for dash.latvi.space |
| `LATVI_PASSWORD` | ✅ | Login password |
| `PROXY` | ⚠️ | Proxy URL (e.g. `socks5://...` or `http://...`). Needed for linkvertise farming. If empty, only the daily reward runs. |
| `TG_BOT_TOKEN` | ⬜ | Telegram bot token for notifications |
| `TG_CHAT_ID` | ⬜ | Telegram chat ID for notifications |
| `MAX_CLAIMS` | ⬜ | Max linkvertise claims per run (default `20`) |

> The proxy is routed through a local **GOST** tunnel (`127.0.0.1:8080`) to keep a single consistent IP across the full shortlink flow (avoids linkvertise anti-bot IP hops).

## Notes

- The daily reward works **without any proxy** — only the linkvertise farming step needs one.
- GOST tunnel and screenshot steps are marked `continue-on-error`, so a failure there won't turn the whole run red.
- Free GitHub runners may queue during peak hours (can take 10–30 min to start).

## Changelog

### 2026-07-09 — Fixed broken workflow
All runs were failing with `Invalid workflow file: .github/workflows/latvi.yml#L70`.

Root cause: the **Debug HTML dump** step contained a multi-line `python3 -c "..."` block that was not indented correctly inside the YAML `run: |` block, making the entire workflow file invalid (GitHub parsed zero steps).

Fixes applied:
1. `latvi_coins.py`: fixed an `IndentationError` in `daily_reward()` (`with open(...)` block).
2. Removed the malformed Debug HTML dump step.
3. Added `continue-on-error: true` to the GOST tunnel and screenshot steps.
4. Restored clean `schedule` + `workflow_dispatch` triggers (temporary `push` trigger used for testing was removed).

Verified: run **#70** completed successfully.

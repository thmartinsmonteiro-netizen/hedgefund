# Paper fund: special situations

A notional hedge fund (US$100,000 start, 2026-09-09) that runs the mandate in `mandate/` as if it were live. Every mark and every trade is a git commit, so nothing can be backfilled quietly. The point is a track record for a Starboard proposal, built while the real IBKR account is in phase 1.

## Layout
- `data/` the fund, as CSV. `positions.csv` (ticker universe and status), `trades.csv`, `cashflows.csv`, `prices.csv`, `pipeline.csv`, `rejected.csv`, `closed.csv`, `assumptions.json`.
- `scripts/mark.py` daily price fetch (Yahoo via yfinance); `scripts/nav.py` NAV, benchmarks, limits; `scripts/build_xlsx.py` rebuilds `reports/tracker.xlsx`.
- `reports/` generated: `nav.csv`, `positions_latest.csv`, `summary.md`, `tracker.xlsx`. Do not edit by hand.
- `memos/` weekly memos, `YYYY-Www.md`.
- `mandate/` the constitution: mandate, screens, holdings, memo template.
- `routines/` how the daily mark (GitHub Actions) and the weekly memo (Claude Code routine) are scheduled.

## Setup, once
1. Create a private GitHub repo and push this folder. Enable Actions. The daily mark starts running on the next weekday at 18:30 Sao Paulo; trigger it once by hand from the Actions tab to confirm Yahoo returns the Athens and B3 closes.
2. Replace the placeholders in `data/prices.csv` (2026-09-09 row), `data/trades.csv` (EURUSD 1.17 and the 4 Sep EYDAP price) and `data/assumptions.json` (costs, cash rate, IWDA ticker) with actuals. Commit.
3. In Claude Code, open the repo and run `/schedule`, using `routines/weekly-memo.md` as the prompt, weekly on Wednesday. Approve each memo PR yourself; the routine never merges.

## Weekly, you
Read the PR. Merge it or reject it. Answer the "For you to decide" questions in the PR or in the next memo's issue. Book dividends and the annual 15% tax in `cashflows.csv`. That is the whole job.

## Honesty rules (from the mandate)
Closes only, never intraday. Missing closes stay missing and the NAV row is flagged. Costs on every paper trade. Exits at the close of the day the memo says so, including forced exits at catalyst dates. Benchmarks: the same money in the core ETF, and USD cash.

## Tokens
The daily leg is a cron job with no model call. The only model spend is the weekly memo, which is where judgment is needed.

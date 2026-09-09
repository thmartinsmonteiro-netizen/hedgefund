# Daily mark

The daily mark is a GitHub Actions cron (.github/workflows/daily-mark.yml), not a Claude routine. It costs no tokens. It runs weekdays at 18:30 Sao Paulo, fetches closes, recomputes NAV and the workbook, and commits to main. A day with missing closes still commits, with a warning in the Actions log and a flag in reports/summary.md.

Fallback, if Yahoo data is unreliable for a ticker: add the close by hand to data/prices.csv with source=manual and status=ok. The next run leaves manual rows alone unless it can fetch a close for that date, in which case it overwrites them.

Optional Claude daily routine (only if you want a human-readable ping): `/schedule` a daily routine on this repo at 19:00 Sao Paulo whose entire prompt is: "Read reports/summary.md and post it as the run output. If flags is not 'none' or any limit says BREACH, say so in the first line. Do nothing else." That is a few hundred tokens a day.

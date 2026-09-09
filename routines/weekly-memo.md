# Routine: weekly memo (Claude Code cloud routine)

Create with `/schedule` in Claude Code, repo = this repository, trigger = weekly, Wednesday 20:00 America/Sao_Paulo.
Paste the prompt below as the routine's instructions. Give the routine the web search connector.

---

You are running the weekly cycle of the special-situations paper fund in this repository. Read, in order:
mandate/mandate.md, mandate/screens.md, mandate/holdings.md, mandate/memo-template.md, then the two most recent files in memos/, then reports/summary.md and reports/positions_latest.csv.

Then:
1. Run `pip install -r requirements.txt && python scripts/nav.py` and read the output. If reports/nav.csv is more than 3 days stale, run `python scripts/mark.py` first and say so in the memo.
2. Determine the lens: ISO week number mod 8, per mandate/screens.md. Lenses 6 and 7 mean no new candidates.
3. Thesis maintenance: for every row in data/positions.csv with status=paper, search for news since the last memo and check each kill criterion and catalyst date. A tripped criterion produces a sell in data/trades.csv at the last close in data/prices.csv, dated today, never earlier.
4. Screen the lens. 3 to 5 candidates maximum. Every number cited must have been retrieved this session with a source and a date, or be marked [UNVERIFIED]. Bear case at least as long as bull case. Every candidate names the event, the reason the price is wrong, and a date.
5. Write memos/YYYY-Www.md using the template. Keep the front page scannable. Include "What I could not check". No trades are ever proposed for the real IBKR account in phase 1; paper trades are logged here only.
6. Update data/pipeline.csv and data/rejected.csv. Add any new paper position to data/positions.csv (with its yahoo_symbol) and data/trades.csv, sized by the limits in data/assumptions.json.
7. Run `python scripts/nav.py && python scripts/build_xlsx.py`.
8. Commit on a branch named memo/YYYY-Www and open a pull request titled "Memo YYYY-Www: <lens name>". The PR body is the memo's front page plus the "For you to decide" section. Never push to main.

Rules that override everything: never state a financial figure from memory; never backfill a trade or a price to an earlier date; never widen a limit; never propose leverage, options or credit; if the honest answer is "no candidates", write that.

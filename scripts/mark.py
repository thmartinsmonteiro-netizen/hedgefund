"""Daily mark: fetch closes for every symbol the fund needs and append to data/prices.csv.

Rules (from the mandate's honesty section):
- A price is a close, never intraday. If the source returns no close for the mark date,
  the row is written with status=missing and no number. NAV then carries the last good
  close and flags the position as stale. Nothing is invented.
- Symbols are the union of: every ticker in positions.csv (any status), every FX pair in
  assumptions.json, and the core benchmark.
- Idempotent: running twice on the same date replaces that date's rows.

Usage:
    python scripts/mark.py                 # mark today (or last business day if weekend)
    python scripts/mark.py --date 2026-09-10
    python scripts/mark.py --dry-run       # print, do not write
"""
import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_assumptions():
    return json.loads((DATA / "assumptions.json").read_text())


def symbols_needed(a):
    pos = pd.read_csv(DATA / "positions.csv")
    syms = [s for s in pos["yahoo_symbol"].dropna().unique()]
    syms += list(a["fx_symbols"].values())
    syms.append(a["core_benchmark"])
    return sorted(set(syms))


def last_business_day(d):
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def fetch_closes(symbols, mark_date):
    """Return {symbol: (close or None, source)} for mark_date using yfinance.
    Looks back 7 days so a holiday on one exchange does not kill the run; the close is
    taken only if its date == mark_date, otherwise None (missing)."""
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed; pip install -r requirements.txt", file=sys.stderr)
        return {s: (None, "yfinance-unavailable") for s in symbols}
    out = {}
    start = mark_date - timedelta(days=7)
    end = mark_date + timedelta(days=1)
    for s in symbols:
        try:
            h = yf.Ticker(s).history(start=start.isoformat(), end=end.isoformat(), auto_adjust=False)
            if h is None or h.empty:
                out[s] = (None, "yfinance-empty")
                continue
            h.index = pd.to_datetime(h.index).date
            if mark_date in h.index and pd.notna(h.loc[mark_date, "Close"]):
                out[s] = (round(float(h.loc[mark_date, "Close"]), 6), "yfinance")
            else:
                out[s] = (None, f"yfinance-no-close-on-{mark_date}")
        except Exception as e:  # noqa: BLE001
            out[s] = (None, f"yfinance-error:{type(e).__name__}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD; default last business day")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    a = load_assumptions()
    mark_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else last_business_day(date.today())
    syms = symbols_needed(a)
    closes = fetch_closes(syms, mark_date)

    rows = []
    for s in syms:
        c, src = closes[s]
        rows.append({"date": mark_date.isoformat(), "symbol": s,
                     "close": "" if c is None else c, "source": src,
                     "status": "ok" if c is not None else "missing"})
    new = pd.DataFrame(rows)

    prices_path = DATA / "prices.csv"
    old = pd.read_csv(prices_path, dtype=str) if prices_path.exists() else pd.DataFrame(columns=new.columns)
    old = old[old["date"] != mark_date.isoformat()]
    merged = pd.concat([old, new.astype(str)], ignore_index=True).sort_values(["date", "symbol"])

    missing = [r["symbol"] for r in rows if r["status"] == "missing"]
    print(f"Mark {mark_date}: {len(syms) - len(missing)} ok, {len(missing)} missing {missing}")
    for r in rows:
        print(f"  {r['symbol']:<12} {r['close'] if r['close'] != '' else '-':>10}  {r['source']}")

    if args.dry_run:
        return 0
    merged.to_csv(prices_path, index=False)
    # Exit code 2 signals "marked with gaps" so a CI job can surface it without failing.
    return 3 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

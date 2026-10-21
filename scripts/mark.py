"""Price marks: fetch closes for every symbol the fund needs and write data/prices.csv.

Rules (mandate honesty section):
- A price is a daily close, never intraday. The row records the date of the close actually
  used (close_date). If no close is available within `max_lag_days` on or before the mark
  date, the row is written with status=missing and no number; nav.py then carries the last
  good close and flags the position stale.
- status=ok means close_date == mark date; status=lagged means an earlier close within the
  lag window was used (exchange holiday, or the data source posts the bar late).
- Manual rows (source=manual) are never overwritten.
- Idempotent per (date, symbol).

Usage:
    python scripts/mark.py                      # mark the previous business day
    python scripts/mark.py --date 2026-10-20    # mark a specific date
    python scripts/mark.py --backfill           # fill every missing (date, symbol) since fund_start
    python scripts/mark.py --dry-run
"""
import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COLS = ["date", "symbol", "close", "close_date", "source", "status"]


def load_assumptions():
    return json.loads((DATA / "assumptions.json").read_text())


def symbols_needed(a):
    pos = pd.read_csv(DATA / "positions.csv")
    syms = [s for s in pos["yahoo_symbol"].dropna().unique()]
    syms += list(a["fx_symbols"].values())
    syms.append(a["core_benchmark"])
    return sorted(set(syms))


def previous_business_day(d):
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def business_days(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def fetch_history(symbols, start, end):
    """{symbol: Series(close indexed by date)} between start and end inclusive."""
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed; pip install -r requirements.txt", file=sys.stderr)
        return {}
    out = {}
    for s in symbols:
        try:
            h = yf.Ticker(s).history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(),
                                     auto_adjust=False)
            if h is None or h.empty:
                out[s] = pd.Series(dtype=float)
                continue
            ser = h["Close"].dropna()
            ser.index = pd.to_datetime(ser.index).date
            out[s] = ser
        except Exception as e:  # noqa: BLE001
            print(f"  {s}: fetch error {type(e).__name__}", file=sys.stderr)
            out[s] = pd.Series(dtype=float)
    return out


def row_for(symbol, ser, mark_date, max_lag):
    cand = ser[[d for d in ser.index if d <= mark_date and (mark_date - d).days <= max_lag]] if len(ser) else ser
    if len(cand) == 0:
        return {"date": mark_date.isoformat(), "symbol": symbol, "close": "", "close_date": "",
                "source": "yfinance", "status": "missing"}
    cd = max(cand.index)
    return {"date": mark_date.isoformat(), "symbol": symbol, "close": round(float(cand[cd]), 6),
            "close_date": cd.isoformat(), "source": "yfinance",
            "status": "ok" if cd == mark_date else "lagged"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    a = load_assumptions()
    max_lag = int(a.get("max_lag_days", 4))
    syms = symbols_needed(a)
    prices_path = DATA / "prices.csv"
    old = pd.read_csv(prices_path, dtype=str).fillna("") if prices_path.exists() else pd.DataFrame(columns=COLS)
    for c in COLS:
        if c not in old.columns:
            old[c] = ""
    old = old[COLS]

    if args.backfill:
        start = datetime.strptime(a["fund_start"], "%Y-%m-%d").date()
        end = previous_business_day(date.today() + timedelta(days=1))
        targets = [(d, s) for d in business_days(start, end) for s in syms]
    else:
        md = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else previous_business_day(date.today())
        start, end, targets = md, md, [(md, s) for s in syms]

    hist = fetch_history(syms, start - timedelta(days=max_lag + 3), end)
    keep = {(r["date"], r["symbol"]) for _, r in old.iterrows()
            if r["source"] == "manual" or (args.backfill and r["status"] in ("ok", "lagged"))}
    new_rows = [row_for(s, hist.get(s, pd.Series(dtype=float)), d, max_lag)
                for d, s in targets if (d.isoformat(), s) not in keep]
    new = pd.DataFrame(new_rows, columns=COLS)

    key_new = {(r["date"], r["symbol"]) for r in new_rows}
    merged = pd.concat([old[[(r["date"], r["symbol"]) not in key_new for _, r in old.iterrows()]], new.astype(str)],
                       ignore_index=True).sort_values(["date", "symbol"])

    missing = [f"{r['date']}:{r['symbol']}" for r in new_rows if r["status"] == "missing"]
    lagged = sum(1 for r in new_rows if r["status"] == "lagged")
    print(f"{'Backfill' if args.backfill else 'Mark'} {start}..{end}: {len(new_rows) - len(missing)} priced "
          f"({lagged} lagged), {len(missing)} missing")
    for m in missing[:40]:
        print("  missing", m)
    if args.dry_run:
        return 0
    merged.to_csv(prices_path, index=False)
    return 3 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

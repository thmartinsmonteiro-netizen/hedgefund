"""NAV engine. Reads data/*.csv, writes reports/nav.csv, reports/positions_latest.csv,
reports/summary.md. Pure arithmetic; no judgment lives here.

Conventions
- Cash earns cash_rate_annual, accrued daily between mark dates.
- A trade's cash impact = -(gross + cost) for buys, +(gross - cost) for sells, with cost =
  commission + spread (+ fx cost if non-USD), applied at the trade's own fx_to_usd.
- Position MV on a mark date = qty held x last good close x last good fx. If the close used
  is older than stale_after_days, the position is flagged 'stale' in that NAV row.
- Core benchmark = starting NAV in the core ETF bought at the first mark, less one round of
  USD trade cost. Cash benchmark = starting NAV at the cash rate.
- Tax (15% on realised gains) is not automatic: book it in cashflows.csv once a year.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, REPORTS = ROOT / "data", ROOT / "reports"


def load():
    a = json.loads((DATA / "assumptions.json").read_text())
    pos = pd.read_csv(DATA / "positions.csv")
    tr = pd.read_csv(DATA / "trades.csv", parse_dates=["date"])
    cf = pd.read_csv(DATA / "cashflows.csv", parse_dates=["date"])
    px = pd.read_csv(DATA / "prices.csv", parse_dates=["date"])
    px["close"] = pd.to_numeric(px["close"], errors="coerce")
    return a, pos, tr, cf, px


def trade_costs(tr, a):
    tr = tr.copy()
    tr["gross_usd"] = tr["qty"] * tr["price_native"] * tr["fx_to_usd"]
    base = a["commission_pct"] + a["spread_pct"]
    tr["cost_pct"] = [base + (0 if c == "USD" else a["fx_cost_pct"]) for c in tr["ccy"]]
    tr["cost_usd"] = tr["gross_usd"] * tr["cost_pct"]
    tr["signed_qty"] = [q if s == "Buy" else -q for q, s in zip(tr["qty"], tr["side"])]
    tr["cash_impact_usd"] = [-(g + c) if s == "Buy" else g - c
                             for g, c, s in zip(tr["gross_usd"], tr["cost_usd"], tr["side"])]
    return tr


def last_good(px, symbol, on_date):
    """Last non-null close for symbol on or before on_date -> (close, close_date) or (None, None)."""
    h = px[(px["symbol"] == symbol) & (px["date"] <= on_date) & px["close"].notna()]
    if h.empty:
        return None, None
    r = h.sort_values("date").iloc[-1]
    return float(r["close"]), r["date"]


def build_nav():
    a, pos, tr, cf, px = load()
    tr = trade_costs(tr, a)
    start = pd.Timestamp(a["fund_start"])
    nav0 = float(a["starting_nav_usd"])
    rate = float(a["cash_rate_annual"])
    stale_days = int(a.get("stale_after_days", 5))
    fx_syms = a["fx_symbols"]
    bench = a["core_benchmark"]

    dates = sorted(d for d in px["date"].unique() if d >= start)
    if not dates:
        raise SystemExit("No mark dates on or after fund_start in prices.csv")

    rows, cash, prev = [], nav0, None
    bench0 = None
    for d in dates:
        interest = 0.0 if prev is None else cash * rate * (d - prev).days / 365
        lo = pd.Timestamp.min if prev is None else prev
        flows = tr.loc[(tr["date"] > lo) & (tr["date"] <= d), "cash_impact_usd"].sum() \
            + cf.loc[(cf["date"] > lo) & (cf["date"] <= d), "amount_usd"].sum()
        cash = cash + interest + flows

        mv_total, flags, open_names = 0.0, [], 0
        for _, p in pos.iterrows():
            qty = tr.loc[(tr["ticker"] == p["ticker"]) & (tr["date"] <= d), "signed_qty"].sum()
            if qty == 0:
                continue
            open_names += 1
            close, cdate = last_good(px, p["yahoo_symbol"], d)
            fx, fdate = (1.0, d) if p["ccy"] == "USD" else last_good(px, fx_syms[p["ccy"]], d)
            if close is None or fx is None:
                flags.append(f"{p['ticker']}:NO_PRICE")
                continue
            if (d - cdate).days > stale_days or (d - fdate).days > stale_days:
                flags.append(f"{p['ticker']}:stale({cdate.date()})")
            mv_total += qty * close * fx

        nav = cash + mv_total
        b_close, _ = last_good(px, bench, d)
        if bench0 is None and b_close is not None:
            bench0 = b_close
        cost_usd = a["commission_pct"] + a["spread_pct"]
        bench_cum = None if (b_close is None or bench0 is None) else b_close / bench0 * (1 - cost_usd) - 1
        cash_cum = (1 + rate) ** ((d - dates[0]).days / 365) - 1
        rows.append({"date": d.date(), "cash_usd": round(cash, 2), "positions_mv_usd": round(mv_total, 2),
                     "interest_usd": round(interest, 2), "net_flows_usd": round(flows, 2),
                     "nav_usd": round(nav, 2), "open_positions": open_names,
                     "core_bench_cum": None if bench_cum is None else round(bench_cum, 6),
                     "cash_bench_cum": round(cash_cum, 6), "flags": ";".join(flags)})
        prev = d

    nav = pd.DataFrame(rows)
    nav["daily_return"] = nav["nav_usd"].pct_change().fillna(0).round(6)
    nav["cum_return"] = (nav["nav_usd"] / nav0 - 1).round(6)
    nav["drawdown"] = (nav["nav_usd"] / nav["nav_usd"].cummax() - 1).round(6)
    nav["alpha_vs_core"] = (nav["cum_return"] - nav["core_bench_cum"]).round(6)
    nav["alpha_vs_cash"] = (nav["cum_return"] - nav["cash_bench_cum"]).round(6)
    return a, pos, tr, px, nav


def positions_latest(a, pos, tr, px, nav):
    d = pd.Timestamp(nav["date"].iloc[-1])
    latest_nav = float(nav["nav_usd"].iloc[-1])
    out = []
    for _, p in pos.iterrows():
        h = tr[(tr["ticker"] == p["ticker"]) & (tr["date"] <= d)]
        qty = h["signed_qty"].sum()
        cost = -h["cash_impact_usd"].sum()
        close, cdate = last_good(px, p["yahoo_symbol"], d)
        fx, _ = (1.0, d) if p["ccy"] == "USD" else last_good(px, a["fx_symbols"][p["ccy"]], d)
        mv = None if (qty == 0 or close is None or fx is None) else qty * close * fx
        out.append({"ticker": p["ticker"], "name": p["name"], "status": p["status"], "sleeve": p["sleeve"],
                    "country": p["country"], "qty": qty, "cost_basis_usd": round(cost, 2) if qty else None,
                    "last_close": close, "close_date": None if cdate is None else cdate.date(),
                    "mv_usd": None if mv is None else round(mv, 2),
                    "pnl_usd": None if mv is None else round(mv - cost, 2),
                    "pnl_pct": None if (mv is None or cost == 0) else round(mv / cost - 1, 4),
                    "pct_nav": None if mv is None else round(mv / latest_nav, 4),
                    "target_price": p["target_price"],
                    "upside_to_target": None if (close is None or pd.isna(p["target_price"])) else round(p["target_price"] / close - 1, 4),
                    "catalyst_date": p["catalyst_date"],
                    "days_to_catalyst": None if pd.isna(p["catalyst_date"]) else (pd.Timestamp(p["catalyst_date"]) - d).days,
                    "kill_criteria": p["kill_criteria"]})
    return pd.DataFrame(out), latest_nav


def limit_checks(a, plat, latest_nav):
    L = a["limits"]
    held = plat[plat["qty"].fillna(0) > 0]
    msgs = []
    if not held.empty:
        w = (held["cost_basis_usd"] / latest_nav).max()
        msgs.append(("Largest position at cost", f"{w:.1%}", "BREACH" if w > L["max_position_at_cost"] else "ok"))
        n = (held["sleeve"] == "Satellite").sum()
        msgs.append(("Satellite names", str(n), "BREACH" if n > L["max_satellite_names"] else "ok"))
        br = held.loc[held["country"] == "Brazil", "pct_nav"].fillna(0).sum()
        msgs.append(("Brazil % NAV", f"{br:.1%}", "BREACH" if br > L["brazil_cap"] else "ok"))
        fs = held.loc[held["sleeve"] == "Fast", "pct_nav"].fillna(0).sum()
        msgs.append(("Fast sleeve % NAV", f"{fs:.1%}", "BREACH" if fs > L["fast_sleeve_cap"] else "ok"))
    else:
        msgs.append(("Positions", "none", "ok"))
    return msgs


def main():
    a, pos, tr, px, nav = build_nav()
    REPORTS.mkdir(exist_ok=True)
    nav.to_csv(REPORTS / "nav.csv", index=False)
    plat, latest_nav = positions_latest(a, pos, tr, px, nav)
    plat.to_csv(REPORTS / "positions_latest.csv", index=False)
    checks = limit_checks(a, plat, latest_nav)
    last = nav.iloc[-1]
    lines = [f"# Paper fund summary, {last['date']}", "",
             f"NAV US${last['nav_usd']:,.0f} | cum {last['cum_return']:+.2%} | core bench "
             f"{'n/a' if pd.isna(last['core_bench_cum']) else f'{last['core_bench_cum']:+.2%}'} | "
             f"cash bench {last['cash_bench_cum']:+.2%} | drawdown {last['drawdown']:.2%} | open {int(last['open_positions'])}",
             f"Flags: {last['flags'] or 'none'}", "", "## Limits"]
    lines += [f"- {k}: {v} ({s})" for k, v, s in checks]
    lines += ["", "## Positions held"]
    held = plat[plat["qty"].fillna(0) > 0]
    for _, r in held.iterrows():
        lines.append(f"- {r['ticker']} qty {int(r['qty'])} | MV {r['mv_usd']} | P&L {r['pnl_pct'] if r['pnl_pct'] is None else f'{r['pnl_pct']:+.2%}'} "
                     f"| {r['pct_nav'] if r['pct_nav'] is None else f'{r['pct_nav']:.1%}'} NAV | catalyst in {r['days_to_catalyst']} d | close {r['close_date']}")
    lines += ["", "## Catalysts and gates within 14 days"]
    soon = plat[plat["days_to_catalyst"].notna() & (plat["days_to_catalyst"] <= 14)]
    lines += [f"- {r['ticker']}: {r['catalyst_date']} ({r['days_to_catalyst']} d)" for _, r in soon.iterrows()] or ["- none"]
    (REPORTS / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

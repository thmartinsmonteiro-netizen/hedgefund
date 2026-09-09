# Mandate amendments

Dated changes to mandate.md and screens.md. The originals are kept untouched so the record shows what changed and when. Where an amendment conflicts with the original, the amendment wins.

## A1, 2026-09-09: instruments, geography and conflicts

Decided by the user in conversation, effective for the paper fund only. The real IBKR account keeps the original mandate.

1. **Derivatives allowed.** Listed options and futures may be used, long or short, and equity may be sold short. Purpose: to express event-driven views with defined risk (options into a dated catalyst), to hedge the acquirer leg of stock-for-stock merger arbitrage, and to hedge market or currency exposure the thesis does not want. Rules that come with this:
   - Long option premium at risk: at most 5% of NAV in aggregate; a single option position at most 2% of NAV in premium. Premium is assumed lost at expiry unless the position is closed in a memo.
   - Short options only when covered by the underlying or as part of a spread whose maximum loss is defined and counted against the 8% single-position cap.
   - Short equity: at most 5% of NAV per name at cost, only against a dated event, borrow assumed available at 1% per year unless the memo states a higher rate; hard-to-borrow names are not shorted.
   - Gross exposure capped at 150% of NAV, net exposure kept between minus 50% and plus 120% of NAV. Limits live in assumptions.json and are checked in reports/summary.md.
   - Futures are sized by notional against the same caps; margin is treated as cash reserved and earns the cash rate.
   - Every derivative row in positions.csv carries instrument, multiplier, underlying and expiry. Pricing: listed options and futures via the daily feed where the symbol resolves; otherwise the memo enters the close by hand with source=manual. A derivative with no price for five days is flagged stale like any other line.
   - The mandate's "no options, futures, margin or crypto" clause is suspended for the paper fund. Crypto stays excluded.
2. **Worldwide assets.** Any listed market with a readable primary-source document trail qualifies; the IBKR-tradeable gate is retained as a preference, not a gate, for the paper fund, and the memo states when a line would not be tradeable in the real account. The US$150,000/day liquidity floor and the 15%-of-ADV rule are unchanged. The 0 to 10% Brazil cap is unchanged.
3. **Starboard conflict screen removed.** The paper fund no longer excludes or gates names on the basis of the user's employer's activity. The memo still states, once, whether a situation is one the user has direct professional knowledge of, because that is disclosure the track record will need later.
4. **Unchanged, deliberately.** The factor exclusion (no highly levered companies, banks, specialty lenders, commercial real estate, BDCs or listed alternative managers in the satellite; post-reorg equities only below 2.5x at emergence) stays, because it exists for salary correlation, not for conflicts. The user can lift it with a further dated amendment. The weekly cadence, the eight-lens rotation, the bi-monthly gates, the honesty rules and the "nothing backfilled" rule stay.

Consequences for the record: Light (LIGT3) is no longer gated on the Starboard question, only on the emergence-leverage test. Oncoclinicas (ONCO3) is still rejected under item 4 unless the fast-sleeve question in memo W37 is answered in its favour. AySA and Metrogas may now be written up.

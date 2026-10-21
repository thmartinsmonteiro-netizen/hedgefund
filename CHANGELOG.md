# Changelog of data corrections

Trades and prices are never backdated. When a stored number was wrong, the correction is logged here with the date it was made, so the record shows what was known when.

- 2026-10-21: EYDAP.AT had no close in prices.csv on 29 of 30 mark dates since 2026-09-09; IWDA.L, SAPR11.SA, LIGT3.SA and BRLUSD=X had sporadic gaps. Cause: the daily job ran at 21:30 UTC and required a bar dated exactly the mark date, and Yahoo posts some exchanges' bars late or under a different date. Effect: NAV from 2026-09-09 to 2026-10-21 valued EYDAP at zero (a false -7.6%). Fix: mark.py accepts the latest close within 4 days (status=lagged), the job now marks the previous business day at 06:00 Sao Paulo, and a one-off backfill refetches every missing (date, symbol) since fund start. NAV history is recomputed from corrected prices; no trade or decision is changed.
- 2026-10-21: EYDAP sell booked at EUR 13.94, the Boerse Stuttgart quote on the decision date, pending the ATSE close from the backfill. Entry price and dates unchanged.
- 2026-10-21: Process failure logged: no weekly memo exists for weeks 38 to 42 because the weekly scheduled task was never created. Those weeks are not reconstructed. The EYDAP catalyst (30 Sep) was checked 21 days late.
- 2026-10-21 (later): backfill delivered the ATSE close for 21 Oct, EUR 13.96; the EYDAP sell is restated from the Stuttgart proxy 13.94 to 13.96 as announced above. Date unchanged.

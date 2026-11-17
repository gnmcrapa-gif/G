# BTC Quant Desk — permanent pre-report audit and critical review

Date: 2026-11-17
Protocol revision: V5.6.0
Branch: `audit/permanent-pre-report-review`

## Why this revision exists

A full review of the persisted production artifact from daily-research run #54 identified a defect that ordinary unit tests had not covered: `_ridge_predict` returns a one-element NumPy array, and the ledger had serialized that array as text such as `[-0.0006588]`. The matured-score path later called `float()` on that string. Once the first forecast matured, this could prevent scoring and block the daily run. New forecasts are now stored as finite scalar floats; the parser accepts the legacy one-element array representation so old append-only records remain scoreable without rewriting history.

## Permanent review sequence

The report generator now runs `build_pre_report_review` before serializing `reports/latest/run_report.json`. The prior `n - 365` rolling cutoff has been replaced with a fixed 2025-11-17 UTC start; the diagnostic window expands, but those rows never re-enter training or tuning. It also emits FACT/INTERPRETATION/HYPOTHESIS/FORECAST sections, a price snapshot, fixed 1/7/30-session observed drivers, pending point forecasts and a closing assessment. A report cannot be emitted as complete when a critical pre-report check fails. The risk gate is forced to paper-only and 0% theoretical exposure if the audit blocks or itself raises an exception.

Every run performs all core checks:

1. Raw-object existence, byte-size and SHA-256 verification for every manifest object.
2. Binance archive-by-archive completeness: expected monthly archives, expected daily files for the current month, exact row counts, failures, duplicates and total calendar-row reconciliation.
3. Bitstamp raw-page reconciliation: total raw page rows, explicit overlap duplicates, canonical rows and at most one filtered unclosed current-day row.
4. UTC target/execution semantics, including an independent synthetic check of the production h+2 open-to-open target.
5. Historical holdout governance: no training on the reused historical continuity window and no claim that it is globally unseen.
6. Append-only forecast-ledger integrity: unique event IDs, finite scalar forecasts, legacy singleton-array compatibility, future entry, expiry ordering and score-to-forecast linkage.
7. Venue quote separation: Binance USDT and Bitstamp USD remain distinct, with no implicit FX conversion or volume pooling.
8. Report-status consistency: a COMPLETE report requires both primary QA passes and a scored-but-not-promoted research result.
9. Benchmark governance: zero-return champion retained, Ridge challenger not promoted.
10. Risk fail-safe: paper-only, no live trading, theoretical exposure exactly 0%.
11. Any forecast whose expiry is already present in the latest validated daily series must have a SCORE event; otherwise the pre-report gate blocks. Invalidated late-entry records remain preserved and are explicitly exempt from the valid-forecast chronology rule.
12. Prospective sample and economic validity gate: 200 matured forecasts per horizon, documented execution rule and fee/spread/slippage model are required before cost-adjusted strategy claims.
9. Optional Coinbase/Kraken source availability and explicit warning when unavailable.
10. Historical outlier cross-check and limitations.

One additional deep-review lens rotates on every run through six domains: data provenance/coverage; execution timing; ledger maturity; statistical validation/multiple testing; risk/economic limits; code efficiency/operations. The rotation key is the UTC run-start epoch second, so reruns on the same day can inspect a different domain. Rotation changes the emphasis, not the baseline: all core checks run every time. The selected lens and evidence are included in the report.

## Historical raw-data audit

The persisted artifact from run #54 contains 133 source objects. Independent local verification of the downloaded artifact found:

- Binance: 127 objects; 111 expected monthly archives from 2017-08 through 2026-10 plus 16 daily archives for 2026-11-01 through 2026-11-16. All expected months/days and row counts were present.
- Bitstamp: 4 raw JSON pages, 4,000 raw page rows, 349 explicit duplicate rows removed at page boundaries, 3,650 canonical daily rows, and one unclosed current-day row excluded.
- Coinbase: 1 recent cross-check object, 300 rows.
- Kraken: 1 recent cross-check object, 720 rows.
- All 133 raw objects matched both manifest byte size and SHA-256. No missing object or hash mismatch was observed in the artifact.

### 2022-11-08 Binance volume tail

Raw Binance BTCUSDT daily kline for 2022-11-08:

- Open 20,590.67 USDT; high 20,700.88 USDT; low 17,166.83 USDT; close 18,547.23 USDT.
- Base volume 760,705.362783 BTC.

Raw Bitstamp BTC/USD daily OHLC for the same UTC candle:

- Open 20,591.00 USD; high 20,669.00 USD; low 17,114.00 USD; close 18,550.00 USD.
- Base volume 12,035.90178845 BTC.

Binance-vs-Bitstamp price differences were approximately -0.0016% open, +0.1542% high, +0.3087% low and -0.0149% close. The price path is corroborated. Binance base volume was about 63.20 times Bitstamp base volume. Venue-specific volume is not interchangeable, so this ratio is not evidence of an erroneous print. Coinbase and Kraken data retrieved in run #54 do not cover 2022-11-08; independent historical volume verification remains unresolved and is explicitly reported as a warning.

## Statistical and prospective status

- The fixed-start expanding historical continuity window beginning 2025-11-17 UTC remains diagnostic-only and is not globally unseen evidence.
- The production target is `log(Open[t+h+2]/Open[t+2])` because the scheduled job runs at 16:00 UTC; h+1 would backdate entry.
- Zero-return remains the frozen champion. Drift and momentum remain benchmarks. Ridge remains challenger-only.
- No calibrated probabilities are permitted until at least 200 genuinely matured prospective SCORE events per horizon plus a separate calibration study.
- The prospective ledgers are not backfilled. Price-only Ridge and OHLCV forecasts use separate append-only ledgers. The OHLCV challenger uses fixed alpha 100 and only pre-2025-11-17 training labels; it does not tune or train on the fixed-start expanding historical continuity window. A forecast only becomes a score after its actual entry and expiry opens exist.
- No strategy PnL, funding, fee-tier, spread or slippage backtest is claimed. An executable economic backtest remains blocked until a trading rule, execution venue, fee tier and realistic fill assumptions are explicitly specified and prospective predictive value exists.
- Risk Overlay v1.1 remains paper-only; theoretical exposure 0%; no orders or auto-trading.

## Tests added

- Monthly archive and daily-file completeness, including deliberate missing-month failure.
- Bitstamp page-row reconciliation.
- Raw manifest byte-size and SHA-256 verification.
- Outlier event-date OHLC corroboration versus venue-specific volume caution.
- Forecast scalar serialization and legacy-array matured scoring.
- Prospective summary compatibility with old append-only ledger records.
- Rotating audit-lens uniqueness.

## Release rule

Do not promote a challenger or change the champion based on this audit. Merge only after CI tests and lint pass and the daily-research workflow completes with the mandatory pre-report audit. If the pre-report gate is BLOCKED, the report must say so and theoretical exposure must remain 0%.


## V5.5-OHLCV-001 prospective implementation

The registered OHLCV hypothesis is no longer merely a proposal. A separate feature pipeline and ledger now emit prospective point forecasts using:
- price-only lagged return and volatility features;
- log-volume surprise relative to the preceding 30 completed sessions and a robust z-score;
- candle range, body, upper/lower wick and close-location features.

Ridge alpha is fixed at 100 and is not tuned on the historical holdout. Training labels are purged so their exit opens occur before the fixed 2025-11-17 UTC cutoff. The latest signal uses current point-in-time features, but no outcome from the historical continuity holdout is used for fitting or tuning. Forecasts are stored in `ledger/ohlcv_challenger_ledger.csv`, separate from the price-only ledger. Old forecasts are never backfilled. The challenger remains NOT_PROMOTED until at least 200 matured prospective observations per horizon, positive lift under HAC/Holm comparisons, stable regime diagnostics, separate calibration evidence and positive cost-adjusted economic value.

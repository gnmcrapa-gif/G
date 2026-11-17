# BTC Quant Desk Protocol V5.6

V5.6 adds a mandatory, independently coded pre-publication review gate. It is a governance and evidence-quality change, not a model promotion. Zero-return remains the frozen champion; drift and momentum remain benchmarks; Ridge remains an unpromoted challenger. Risk Overlay v1.1 remains paper-only and theoretical exposure is 0%.

## 1. Report publication gate

Every scheduled or manual research run must execute the review **after acquisition, QA, scoring and ledger reconciliation, but before serializing `run_report.json`**. The report is still written on failure so the failure itself is auditable; a failed review forces status `BLOCKED`, live trading false and theoretical exposure 0%.

The review is executable code, not a narrative assertion. Its checks and evidence are stored in `pre_report_review`. A report must include:
- review version, run ID, UTC timestamp and explicit `executed_before_report_serialization=true`;
- each check ID, category, PASS/FAIL/WARN, blocking flag and evidence;
- six review cycles: protocol, data, quant, ledger, risk and red-team;
- blocking failures, warnings, publication gate and final decision;
- one rotating adversarial lens selected from volume outlier, close-return outlier, intraday-range outlier and ledger replay. The lens is keyed by GitHub run ID; all mandatory invariants still run on every execution.

The review is fail-closed. Missing files, missing provenance, inconsistent timestamps, failed primary QA, target mismatch, leaked holdout, orphan/duplicate ledger events, or any nonzero/live risk state block publication. Optional Coinbase/Kraken outages are disclosed as WARN, not misrepresented as a successful cross-check.

## 2. Data lineage and archive completeness

- Primary inputs are Binance spot BTCUSDT (USDT quote) and Bitstamp BTC/USD (USD quote). They remain separate; no silent FX conversion or merged price series.
- Both primary venues must have at least five years of daily history and be current through the previous UTC daily candle.
- Every downloaded raw object is rechecked before report publication for path existence, exact byte size and SHA-256. The manifest must retain URL, retrieval timestamp, schema/parser version, venue, symbol and quote.
- Binance archive completeness is checked against expected monthly archive keys and every current-month daily archive key, in addition to OHLCV cadence.
- Bitstamp pagination accounting reconciles raw page rows, overlap duplicates, parsed rows and at most one excluded still-forming current-day candle.
- OHLCV invariants, timezone, closed-candle status, duplicate timestamps, daily gaps, freshness, zero-volume frequency and tail diagnostics remain mandatory.
- Coinbase and Kraken are recent independent checks where available. Quote-basis differences are disclosed; venue-specific volume levels are never compared as if they were the same market.

## 3. Anomaly and event review

Each run records cross-venue context for the maximum volume surprise, largest close-to-close return and largest intraday range. For each event it records the date, venue-specific OHLCV, return, range and volume relative to that venue's own trailing 90-session median. It also records the absolute close-return difference across primary venues when both observations exist.

Volume is venue-specific. A volume spike on Binance is not expected to equal Bitstamp volume. The purpose is to test whether the event is also visible in independent price/range data, not to demand equal turnover. A discrepancy is surfaced for review rather than silently normalized.

## 4. Execution-time and statistical integrity

The scheduled job runs at 16:00 UTC. `Open[t+1]` has already occurred at issuance, so the production executable target is `log(Open[t+h+2]/Open[t+2])`. The theoretical h+1 target is not called executable. Research, validation purge boundaries and ledger derive their timing from the shared execution-lag constant.

- Point-in-time price-only features use data available at signal close.
- Chronological expanding folds, purge/embargo and validation-only tuning remain mandatory.
- The previously inspected historical holdout remains continuity diagnostics only; it is not globally unseen evidence and cannot be recycled for promotion.
- Compare zero-return, drift, momentum and Ridge for horizons 1, 3, 7 and 30. Report loss tails, HAC paired-loss comparisons and Holm multiple-testing adjustment.
- Regime slices are descriptive unless sample sizes and inferential methods justify more.
- Only prospective append-only SCORE events count as matured forecast evidence. Historical holdout rows never count toward the 200-per-horizon probability gate.
- No probability is published without at least 200 matured prospective forecasts per horizon and a separate calibration analysis with uncertainty.

## 5. Ledger and risk

The ledger remains append-only and event-sourced. Every SCORE must reference a FORECAST; duplicate event IDs, backdated entries, invalidated forecasts and premature outcomes are rejected or explicitly invalidated. Pending forecasts are not scored.

No orders, auto-trading or live position sizing are permitted. Risk Overlay v1.1 remains paper-only. Any data QA or pre-report review failure means theoretical exposure 0%.

## 6. Snapshot and efficiency

The report includes a separate last-closed-daily-candle snapshot for Binance BTCUSDT and Bitstamp BTC/USD: timestamp, retrieval time, OHLC, volume, prior close and one-session percentage change. It is explicitly **not** a live spot quote. USD and USDT values are never combined.

The report records acquisition/QA, walk-forward, pre-report review and total runtime. Efficiency is monitored against the workflow timeout; no optimization may remove integrity checks or weaken statistical safeguards merely to shorten execution.

## 7. Required report taxonomy

Every conclusion is labelled FACT, INTERPRETATION, HYPOTHESIS or FORECAST. Each numeric result carries source, venue/quote, unit, observation window, timestamp/timezone and QA state. Derived data such as ETFs, derivatives, on-chain and macro indicators are omitted unless the actual run retrieves a documented series with timestamps and quality evidence.

The report closes with three observed drivers, the principal limitation, evidence that would change the assessment and exactly one next priority experiment. It is emitted on every run, including unchanged or blocked runs.

## 8. Change control and repeated critical review

Only deterministic technical corrections with tests may modify production plumbing. Statistical features/models are isolated challengers. The report must retain a component-by-component audit, falsification conditions, experiment register, changelog and red-team findings. Champion settings and final holdout are immutable unless a separately reviewed governance change explicitly authorizes otherwise.

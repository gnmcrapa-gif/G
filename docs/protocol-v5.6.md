# BTC Quant Desk Protocol V5.6

V5.6 adds a mandatory, independently coded pre-publication review gate. It is a governance and evidence-quality change, not a model promotion. Zero-return remains the frozen champion; drift and momentum remain benchmarks; Ridge remains an unpromoted challenger. Risk Overlay v1.1 remains paper-only and theoretical exposure is 0%.

## 1. Report publication gate

Every scheduled or manual research run must execute the review **after acquisition, QA, scoring and ledger reconciliation, but before serializing `run_report.json`**. The report is still written on failure so the failure itself is auditable; a failed review forces status `BLOCKED`, live trading false and theoretical exposure 0%.

The review is executable code, not a narrative assertion. Its checks and evidence are stored in `pre_report_review`. A report must include:
- review version, run ID, UTC timestamp and explicit `executed_before_report_serialization=true`;
- each check ID, category, PASS/FAIL/WARN, blocking flag and evidence;
- seven review cycles: protocol, data, quant, ledger, risk, operations and red-team;
- blocking failures, warnings, publication gate and final decision;
- one rotating adversarial lens selected from volume outlier, close-return outlier, intraday-range outlier and ledger replay. The lens is keyed by GitHub run ID; all mandatory invariants still run on every execution.

The review is fail-closed. Missing files, missing provenance, inconsistent timestamps, failed primary QA, target mismatch, leaked holdout, orphan/duplicate ledger events, or any nonzero/live risk state block publication. Optional Coinbase/Kraken outages are disclosed as WARN, not misrepresented as a successful cross-check. New forecast, score and invalidation events are staged in memory for review; the append-only ledger and challenger proposal register are written only after the pre-report gate passes. Pull-request runs never mutate the ledger or challenger register. On main, the script appends to the workflow workspace, rereads the ledger, verifies that every prior and proposed event ID is present exactly once, and records the post-append SHA-256. The GitHub persistence step must then successfully commit the files. A failed review therefore cannot persist a new forecast event.

## 2. Data lineage and archive completeness

- Primary inputs are Binance spot BTCUSDT (USDT quote) and Bitstamp BTC/USD (USD quote). They remain separate; no silent FX conversion or merged price series.
- Both primary venues must have at least five years of daily history and be current through the previous UTC daily candle.
- Every downloaded raw object is rechecked before report publication for path existence, exact byte size and SHA-256. The manifest must retain URL, retrieval timestamp, schema/parser version, venue, symbol and quote.
- Binance archive completeness is checked against expected monthly archive keys and every current-month daily archive key, in addition to OHLCV cadence.
- Bitstamp pagination accounting reconciles raw page rows, overlap duplicates, parsed rows and at most one excluded still-forming current-day candle.
- OHLCV invariants, timezone, closed-candle status, duplicate timestamps, daily gaps, freshness, zero-volume frequency and tail diagnostics remain mandatory. Volume outliers use a rolling 90-session median/MAD baseline with the current session excluded and at least 60 prior observations; full-history volume z-scores are not used because volume levels are non-stationary.
- Coinbase and Kraken are recent independent checks where available. Quote-basis differences are disclosed; venue-specific volume levels are never compared as if they were the same market.

## 3. Anomaly and event review

Each run records cross-venue context for the maximum rolling volume surprise, absolute maximum-volume candle, largest close-to-close return and largest intraday range. For each event it records the date, venue-specific OHLCV, return, range and volume relative to that venue's own trailing 90-session median. It also records the absolute close-return difference across primary venues when both observations exist.

Volume is venue-specific. A volume spike on Binance is not expected to equal Bitstamp volume. The purpose is to test whether the event is also visible in independent price/range data, not to demand equal turnover. A discrepancy is surfaced for review rather than silently normalized. When Binance/Bitstamp close prices diverge, the report records their raw price ratio and an explicitly hypothetical implied USD-per-USDT ratio under a BTC-price-parity assumption; it is never presented as an observed FX quote.

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

The report records acquisition/QA, walk-forward, pre-report review and total runtime. It loads the previous persisted report before overwriting it and compares same-venue/same-quote price snapshots, prospective matured counts and benchmark metrics only when the historical evaluation window is identical. Different windows are explicitly marked not comparable. The current code commit, Git ref, workflow run ID and event type are recorded. Efficiency is monitored against the workflow timeout; no optimization may remove integrity checks or weaken statistical safeguards merely to shorten execution.

## 7. Required report taxonomy

Every conclusion is labelled FACT, INTERPRETATION, HYPOTHESIS or FORECAST. Each numeric result carries source, venue/quote, unit, observation window, timestamp/timezone and QA state. Derived data such as ETFs, derivatives, on-chain and macro indicators are omitted unless the actual run retrieves a documented series with timestamps and quality evidence.

The report closes with three observed drivers, the principal limitation, evidence that would change the assessment and exactly one next priority experiment. It is emitted on every run, including unchanged or blocked runs.

## 8. Change control and repeated critical review

Only deterministic technical corrections with tests may modify production plumbing. Statistical features/models are isolated challengers. The report must retain a component-by-component audit, falsification conditions, experiment register, changelog and red-team findings. Champion settings and final holdout are immutable unless a separately reviewed governance change explicitly authorizes otherwise.

## 9. Model-version isolation and remote persistence proof

- Pending forecast idempotency is scoped to signal timestamp, horizon and explicit model version. A new model version may issue its own forecast for the same signal; repeated runs of the same version may not duplicate it.
- Matured prospective errors are grouped by model version. The active version is identified by its latest issuance time; observations from different versions are never pooled into one MAE or sample gate.
- The model version must be incremented whenever forecast features, fitting logic, hyperparameter policy or prediction semantics change. Code commit remains separately recorded for exact provenance.
- After the main-branch persistence push, CI fetches `origin/main` and verifies that the remote ref contains the run's report, manifest, scores, predictions and ledgers byte-for-byte. It rechecks every raw object against manifest size and SHA-256, verifies remote raw-object bytes, and rejects duplicate ledger event IDs. A successful local append/readback alone is not sufficient for the workflow's remote-persistence gate.

## 10. Supplemental public market-context feeds

The report acquires optional public context feeds independently from the price-only forecasting model. These inputs are descriptive context only until separately point-in-time validated and accepted as a challenger feature set.

- Spot: Binance and Bitstamp rolling 24-hour ticker snapshots are labelled last-trade snapshots; daily 1D/7D/30D changes, SMA20/50/200, 20/50-session ranges and ATR14 are calculated from closed daily candles. USD and USDT remain separate.
- Derivatives: Binance USD-M Futures and Bybit Linear public endpoints provide current funding/mark/index, open interest, global long/short account ratios and bounded historical series. Binance open-interest statistics and taker buy/sell ratio endpoints expose only the latest 30 days; Bybit daily OI history is limited to the endpoint's latest 200 observations; funding history has endpoint pagination/record limits. Account ratios describe accounts, not position-weighted leverage.
- Options: Deribit public BTC options chain provides open interest by expiry/strike, put/call OI and volume, ATM IV term structure, and sampled 25-delta skew when ticker Greeks are available. Deribit states options open interest is in underlying BTC units and delayed by 8 hours. Public OI does not reveal dealer-side long/short positioning; net dealer gamma must not be inferred.
- US spot ETFs: The Commoner Bitcoin ETF Tracker by TFTC supplies daily US spot ETF flows, per-fund values, AUM and cumulative flows under CC BY 4.0. The report preserves its update-through date and marks stale sessions. It is not a global ETP dataset.
- Macro/indices: FRED CSV observations include Treasury 2Y/10Y, 10Y real yields, Fed funds, CPI, core PCE, unemployment, payrolls, broad trade-weighted USD, Fed assets, reverse repo, NFCI, S&P 500, Nasdaq Composite, VIX and M2. Each observation keeps its native observation date, unit and freshness limit; release lag is not hidden.
- Exchange gross/net flows and reserves remain unavailable unless a source with documented exchange-wallet labels and coverage is configured. Raw blockchain transfers must not be labelled exchange flows.
- Market-wide long/short liquidations remain unavailable without a verified public feed with coverage and methodology. A private account's own liquidation records are not a market-wide liquidation series.
- CVD: Binance spot and USD-M futures 1h klines expose taker-buy base volume. The report computes hourly aggregated delta as taker-buy base volume minus (total base volume minus taker-buy base volume), summed over rolling 24h/7d/30d windows. This is a reproducible hourly CVD, not tick-level order-book delta and not a cross-venue composite.
- News: GDELT DOC 2.0 searches a rolling 7d BTC/macro/regulation/geopolitics query; official Federal Reserve, SEC, White House and ECB RSS headlines are also ingested. Headline keyword tags are heuristic only. GDELT first-seen timestamps are not publisher publication timestamps. CFTC RSS is recorded as unavailable when disabled by the provider. No sentiment or event-impact score is generated.
- Global ETP flows remain explicitly unavailable until a global source with a documented weekly methodology and data timestamps is separately acquired and tested.

Every optional category must appear in the report coverage matrix as PASS, PARTIAL, STALE, PROXY_ONLY, UNAVAILABLE or NOT_IMPLEMENTED. Optional feed failure never fabricates a value and does not silently become a successful cross-check. All downloaded payloads receive URL, retrieval timestamp, size, SHA-256, schema/parser and source metadata. Optional context is not added to the forecast feature set or used for promotion until a separately pre-registered, point-in-time challenger passes prospective evaluation.

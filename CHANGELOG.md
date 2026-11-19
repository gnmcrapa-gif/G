# Changelog

## [Unreleased] — report consistency

- Derive the reported OHLCV challenger ID from the active protocol version; add a regression assertion so the hypothesis taxonomy and closing experiment reference cannot drift from the registered V5.6 experiment.

## V5.6 — 2026-11-17 (candidate for main)

- Added mandatory executable pre-report review with seven rotating review cycles and a run-ID-selected red-team lens.
- Added raw-object SHA-256/size verification, source manifest completeness, Binance monthly/daily archive coverage and Bitstamp pagination accounting.
- Added rolling 90-session volume surprise diagnostics; withdrew non-stationary full-history volume z-scores.
- Added cross-venue anomaly context for rolling volume surprise, absolute maximum volume, largest close return and largest candle range; quote-basis gaps are disclosed without silently converting USD/USDT.
- Added explicit FACT / INTERPRETATION / HYPOTHESIS / FORECAST sections, last-closed-candle snapshots, economic-validation gates, three observed market factors and a single next experiment.
- Added same-venue/same-quote longitudinal comparison and only compares historical MAE when holdout windows match.
- Staged ledger events are reviewed before append; pull-request runs do not mutate the persistent ledger. Main-branch appends are reread and checked for preservation/uniqueness of all event IDs, with a post-append SHA-256.
- Added legacy one-element-array forecast parsing and scalar serialization so old ledger rows can mature without being lost.
- Derived validation purge boundaries from the shared execution-entry lag constant.
- Added runtime budget, exact code provenance and report publication gates.
- Zero-return champion remains frozen; Ridge remains challenger only; no probabilities or live trading are enabled.

## V5.5.1 — 2026-11-17

- Corrected daily forecast timing for the 16:00 UTC scheduled run: executable entry is Open[t+2], not the already elapsed Open[t+1].
- Centralized target construction for research and ledger.
- Distinguished historical continuity rows from prospective matured ledger outcomes.
- Added initial OHLCV tail and freshness diagnostics.

## [Unreleased] — reliability follow-up

- Make pending-forecast deduplication model-version-aware: one forecast per signal/horizon/version, without suppressing a separately versioned challenger.
- Isolate prospective matured metrics by model version so historical scores from different challenger versions cannot be pooled.
- Add a post-push remote read-back gate that verifies the main ref, report/ledger bytes, all raw-object SHA-256 hashes and sizes, and ledger event-ID uniqueness.
- Refresh README production status and evidence for the verified V5.6 main run.

## [Unreleased] — multisource context extension

- Add timestamped last-trade spot snapshots for Binance and Bitstamp, 1D/7D/30D price changes, moving averages, recent ranges and ATR14.
- Add public Binance USD-M Futures and Bybit Linear funding/open-interest context, with explicit 30-day history limits and taker-flow proxy labels.
- Add Deribit options OI by expiry/strike, put/call ratios, ATM IV term structure and sampled 25-delta skew; disclose the provider's 8-hour OI delay and non-identifiability of dealer positioning.
- Add US spot ETF daily/cumulative flows and AUM from the public TFTC open dataset, preserving update-through date and staleness.
- Add FRED macro and US index observations with native dates, units and freshness checks.
- Add a coverage matrix for exchange reserves/netflows, market-wide liquidations, spot CVD, global ETP flows and geopolitical/regulatory news when no verified source is available.
- Generate a human-readable `daily_report.md` alongside the structured JSON report. Supplemental feeds remain descriptive and do not enter the predictive model until a separate prospective challenger passes.
- Add a same-venue, same-quote BTC halving-cycle comparison at matched elapsed-session horizons, marking cycles without full halving-date history as insufficient.
- Bound FRED acquisition with parallel workers/timeouts; use Binance's public spot market-data mirror for hourly 24h/7d/30d CVD; filter irrelevant news headlines with whole-word tags and mark CFTC news NOT_CONFIGURED rather than asserting an unverified outage.

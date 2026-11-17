# BTC Quant Desk — Target alignment and full-system critical audit

Date: 2026-11-17
Branch: audit/target-alignment-v1
Base commit: f5c8919adf009ec19b00670611f3ea7380db0c11

## Executive decision

Keep zero-return frozen champion. Keep Ridge as unpromoted challenger. Keep Risk Overlay v1.1 paper-only and theoretical exposure at 0%. No new statistical feature is admitted and the historical continuity holdout is not reopened.

## Verified timing facts

- Daily research workflow schedule: 16:00 UTC (`.github/workflows/research.yml`).
- Daily candle indexed by `t` opens at 00:00 UTC on date t and closes at the next 00:00 UTC boundary.
- The next-open target `log(Open[t+h+1]/Open[t+1])` requires entry at the boundary immediately after candle t closes.
- At 16:00 UTC the same day, that entry is already 16 hours old. It is not executable and must not be backdated.
- The first daily open still in the future at scheduled issuance is `Open[t+2]`, so the production executable target is `log(Open[t+h+2]/Open[t+2])`.

## Implemented technical corrections on this branch

1. Centralized target construction in `forward_open_log_return` with explicit `entry_lag_sessions`; default is 2, and 1 is available only for theoretical diagnostics.
2. Research evaluation and prospective ledger now call the same target helper, preventing duplicated formulas from drifting apart.
3. Ledger entry and expiry timestamps derive from the same execution-lag constant; strict future-entry guard remains in force.
4. Added unit tests for h+1 theoretical versus h+2 executable alignment, positive-integer lag validation, and ledger entry timestamp.
5. Added explicit timing metadata to research score output and documented the rationale in protocol/config/README.
6. Renamed the run-report count field from `matured_oos_counts_by_horizon` to `historical_continuity_rows_by_horizon`. Historical holdout predictions are not matured prospective ledger SCORE events; conflating these counts is misleading.

## Full-system critical review

### Data acquisition and provenance — PASS WITH LIMITATIONS
Binance Vision monthly/daily archives and Bitstamp API raw objects are preserved with hashes. Venue and quote currencies are kept separate. Coinbase/Kraken are recent cross-checks, not five-year histories. The QA validator now reports zero-volume frequency, volume median/p99/max and robust-z diagnostic, absolute close-return tails, intraday-range tails, and exact candle-age hours. These are descriptive diagnostics, not automatic rejection thresholds; source-specific candle close semantics and completeness of every expected monthly archive remain open checks. A successful parser is not proof of provider completeness.

### Timestamp, execution, and target alignment — CORRECTED ON THIS BRANCH
The h+1 target is not executable at the scheduled 16:00 UTC issue time. Production target remains h+2 until an intraday execution dataset and point-in-time decision/first-tradable-price methodology are implemented. Do not silently relabel h+2 as h+1.

### Features and model — KEEP FROZEN
Price-only feature construction uses close[t] and lagged values. Ridge is only a challenger. Existing MAE comparisons show no lift over zero-return in the historical continuity diagnostic. No feature additions, retuning on holdout, or automatic champion changes.

### Validation and inference — BLOCKED FOR PROMOTION
Three chronological purged validation folds are present. The final historical window is explicitly reused and not globally unseen. Its metrics are continuity diagnostics only. HAC normal approximations and Holm correction do not repair sample reuse, nonstationarity, or multiple unregistered model families. Regime subsets below 30 are descriptive only. Prospective scoring must use append-only ledger SCORE events only.

### Forecast ledger — PASS WITH GUARDS
The ledger is append-only; late entries are invalidated; matured forecasts are scored against venue-specific Binance opens. Target calculation is now shared with research. Historical prediction counts must never be described as matured ledger counts. No probabilistic claims until at least 200 genuinely matured prospective observations per horizon plus a separate calibration study.

### Risk and economic validity — BLOCKED
Risk Overlay v1.1 remains paper-only. No executable strategy edge, realistic fees/spread/slippage/funding stress, or strategy-level drawdown validation has been established. Theoretical exposure remains 0%; no orders or auto-trading.

### Automation and repository governance — PASS WITH LIMITATIONS
Daily workflow runs at 16:00 UTC and persists evidence. Workflow uses `continue-on-error` around research to allow artifact/report persistence before final failure; this is acceptable only if report status remains BLOCKED and exposure remains zero. Both workflows now pin the current Node 24-compatible checkout/setup-python releases and the artifact upload release to full commit SHAs. This removes the observed Node 20 deprecation warnings and avoids mutable major tags. CI must validate the branch before merge. README and protocol now state the timing rule.

## Remaining priority actions (not silently claimed complete)

- Add source-specific candle close semantics and explicit expected archive/month coverage; the generic zero-volume and tail diagnostics are now implemented, but venue-specific thresholds still require calibration.
- Add an explicit intraday execution study only if the user requires h+1-style execution; do not approximate intraday execution from daily bars.
- Add transaction-cost and turnover modeling only after a forecast challenger shows prospective predictive lift.
- Add point-in-time data availability and revision checks for every optional external series before any feature use.

## Acceptance and release gates

- Unit tests and Ruff pass on this branch.
- GitHub Actions branch CI passes, including the pinned Node 24 action versions.
- No production champion or risk settings are changed.
- No new forecast records are fabricated or backfilled.
- No historical holdout is treated as independent.
- Merge only after CI evidence; otherwise leave branch unmerged and fix failures.

## Reproducibility

All edits are isolated on `audit/target-alignment-v1`; main remains unchanged until explicit merge. This document records design decisions and does not claim that CI has passed before the workflow reports its result.

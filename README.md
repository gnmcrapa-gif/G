# BTC Quant Desk

Research-only BTC quantitative research project. This repository is not an execution engine, auto-trader, or personalized investment advice.

## Current verified status — 2026-11-17

- Protocol: **V5.6.0 audit revision under review**. Mandatory pre-report checks and a six-lens rotating critical review, observed 1/7/30-session drivers and an economic-evidence gate run before report serialization.
- Latest completed production run: [daily-research run 44155330178 — SUCCESS](https://github.com/gnmcrapa-gif/G/actions/runs/44155330178). Acquisition, QA, cross-checks, evaluation, persistence and artifact upload completed.
- Research state: **COMPLETE_NOT_PROMOTED**. Historical holdout is continuity-only; prospective ledger evidence remains insufficient.
- Champion: zero-return baseline. Drift and momentum remain benchmarks. Ridge remains challenger-only and is **not promoted**.
- No calibrated probabilities, no trading orders, and no automatic position sizing.
- Risk Overlay v1.1 remains paper-only; theoretical exposure is 0%.

### Persisted market data

The production run artifact contains 133 raw source objects (485,308 bytes), their manifest, SHA-256 hashes, retrieval timestamps, parser/schema versions, source grades, and provider-terms caveats. An independent check of the downloaded artifact verified every object's byte size and SHA-256. V5.4 adds explicit UTC-offset enforcement and blocks data more than one UTC day behind the current date.

| Source | Quote | Daily rows | Range UTC | Grade | QA |
|---|---|---:|---|---|---|
| Binance BTCUSDT | USDT | 3,379 | 2017-08-17 – 2026-11-16 | A | PASS |
| Bitstamp BTC/USD | USD | 3,650 | 2016-11-19 – 2026-11-16 | A | PASS |
| Coinbase BTC-USD | USD | 300 | 2026-01-21 – 2026-11-16 | B | PASS |
| Kraken XBT/USD | USD | 720 | 2024-11-27 – 2026-11-16 | B | PASS |

All dates are UTC candle-open timestamps; the last complete candle is 2026-11-16. Binance coverage includes all 111 expected monthly archives (2017-08 to 2026-10) and 16 daily archives (2026-11-01 to 2026-11-16). Bitstamp pagination returned 4,000 raw rows; 349 overlapping rows were removed and one unclosed current-day row was excluded before the 3,650-row canonical series was validated. The canonical QA series has no duplicates or daily gaps. USDT/USD quote basis is not FX-adjusted; venues remain separate.

Provider terms apply to public endpoints/archives; no separate legal licensing review is claimed.

### Latest out-of-sample evaluation

Final holdout: **2025-11-16 through 2026-11-15 UTC**, untouched by training or tuning. Target horizons: 1, 3, 7, 30 days. The evaluation uses a one-daily-bar operational latency buffer so ledger entries are genuinely in the future at issue time. Ridge alpha is now selected across three purged, expanding chronological validation folds; the final holdout remains untouched. The report also includes Newey-West HAC paired absolute-loss comparisons (lag h-1 for overlapping targets), Holm family-wise multiple-testing correction, and ex-ante bull/bear/range diagnostics.

MAE is in **log-return units**, not percent. The following metrics are the post-merge V5.4 run on the same untouched historical holdout. The holdout was not used for the three-fold alpha tuning.

| Horizon | OOS n | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE | Ridge vs zero (Holm p) |
|---:|---:|---:|---:|---:|---:|---:|
| 1d | 362 | 0.015894 | 0.015958 | 0.027292 | 0.015956 | 1.000 |
| 3d | 360 | 0.028470 | 0.028681 | 0.049023 | 0.028752 | 0.980 |
| 7d | 356 | 0.042261 | 0.043085 | 0.076872 | 0.043009 | 0.980 |
| 30d | 333 | 0.101414 | 0.102499 | 0.185213 | 0.103350 | 1.000 |

Zero-return has the lowest MAE at every horizon. Ridge therefore remains unpromoted. None of the eight paired comparisons (Ridge vs zero and drift at four horizons) rejects the no-difference null after Holm family-wise correction at 5%. HAC standard errors use max lag h-1 for overlapping target returns. Directional accuracy for the zero-return baseline is reported as not applicable, not as 0%. At least 200 matured OOS forecasts per horizon are available in this holdout, but this alone does not establish calibration or economic value.

### Forecast ledger

`ledger/forecast_ledger.csv` is append-only. Four earlier events were invalidated because their entry timestamps were already past when they were issued; they remain in the ledger for audit and are excluded from scoring. Four current Ridge challenger forecasts are pending, use validation-selected alpha 100, and have future entry time **2026-11-17 00:00 UTC**. They are point estimates only, not trading recommendations or calibrated probabilities.

## Research principles

1. Separate FACT, INTERPRETATION, HYPOTHESIS, and FORECAST.
2. Never claim acquisition, QA, training, backtesting, or validation unless executed and evidenced for that run.
3. Preserve raw data, provenance, hashes, parser/schema versions, and immutable forecast records.
4. Keep venues and quote currencies separate.
5. Use point-in-time features, chronological splits, purge/embargo, and an untouched final holdout.
6. Tune only on validation. Statistical changes remain challengers until independently demonstrated.
7. Abstain when data are stale, incomplete, or fail QA.
8. Do not make probability claims without adequate matured OOS calibration evidence.

## Target and timing

For close index `t` and horizon `h ∈ {1,3,7,30}`:

`y[t,h] = log(Open[t+h+2] / Open[t+2])`

The feature cutoff is the close of candle `t`. One complete daily bar is reserved for operational latency because the daily job runs after the UTC session boundary. Entry is at `Open[t+2]`; expiry is `Open[t+h+2]`. The ledger rejects any entry that is not strictly later than the actual issue timestamp.

## Automation and quick start

GitHub Actions workflow `daily-research` runs daily at **16:00 UTC** and can also be triggered manually. It runs tests and Ruff, acquires data, validates it, evaluates the model, appends the ledger, and persists raw data/manifests/reports. It does not place orders.

Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests scripts
python scripts/run_research.py
```

## Output files

- `data/raw/`: source-native raw archives/responses.
- `reports/latest/data_manifest.json`: URLs, retrieval times, sizes, hashes, schemas, source grades, and terms notes.
- `reports/latest/run_report.json`: source QA, cross-checks, holdout status, ledger activity, and limitations.
- `reports/latest/scores.json`: benchmark and challenger metrics.
- `reports/latest/oos_predictions.csv`: final-holdout predictions and outcomes.
- `ledger/forecast_ledger.csv`: append-only forecast, invalidation, and scoring events.

## Security and limitations

The repository is public. Do not commit credentials, personal data, exchange account exports, or non-public/licensed datasets. This is a price-only research model; no strategy PnL, fees/spread/slippage/funding stress test, regime-stratified significance, multiple-testing correction, derivatives, ETF, options, on-chain, or macro model is claimed. Those gaps must be addressed before any economic or live-trading conclusion.


## V5.4 research upgrade

- Strictly reject naive or non-UTC source timestamps; data must be explicitly UTC.
- Daily crypto data older than one UTC calendar day now blocks the run (yesterday's candle is expected at the 16:00 UTC schedule).
- Ridge alpha tuning uses three expanding chronological validation folds, each purged so validation labels cannot leak into training.
- Report paired absolute-loss differences versus zero-return and training-drift baselines using Newey-West HAC standard errors with horizon-1 lags for overlapping returns. P-values use a normal approximation and are diagnostics, not standalone promotion criteria.
- Report ex-ante bull/bear/range holdout slices. Regime labels use only close versus SMA200 and the 20-session SMA200 slope.
- The V5.3.1 final holdout is not retuned or reused for V5.4 model selection. V5.4 evaluation uses the same historical holdout strictly as a diagnostic continuity check; a future promotion requires a new, untouched prospective period and independent economic tests.


### V5.4 verified execution

- Post-merge run: [daily-research #54 — SUCCESS](https://github.com/gnmcrapa-gif/G/actions/runs/43944304633), 16 November 2026, 19:55:25–19:56:07 UTC.
- Tests: 25 passed; Ruff: all checks passed.
- All four source QA checks PASS; latest closed daily candle 2026-11-15 UTC, age 1 UTC calendar day.
- All four horizons used three expanding, purged validation folds; selected Ridge alpha was 100 for each.
- Holm-adjusted paired-loss p-values for Ridge vs zero: 1.000, 0.980, 0.980, 1.000 for 1d/3d/7d/30d. No family-wise significant lift.
- Ledger is append-only. Run #54 added no new forecast or score event and suppressed four duplicate candidates because four forecasts for the same signal bar were already pending. The pending ledger records are from Ridge challenger 0.3; V5.4's challenger 0.4 will issue only on a new signal bar. No prior record was overwritten.


## V5.5 verified execution

- Merged to main: [PR #5](https://github.com/gnmcrapa-gif/G/pull/5), merge commit `9b7ba1af745638ee59b78ae0c3d877a32a8c283d`.
- Final main-branch run: [daily-research #57 — SUCCESS](https://github.com/gnmcrapa-gif/G/actions/runs/43946659530), 16 November 2026, 20:08:54–20:09:40 UTC.
- Tests: **29 passed**; Ruff: **all checks passed**.
- Binance and Bitstamp primary QA PASS; Coinbase and Kraken recent cross-checks PASS. All source series end at the 2026-11-15 closed UTC candle.
- The historical continuity diagnostic still shows zero-return MAE below Ridge at all four horizons. This is not fresh independent evidence; zero-return remains champion.
- Prospective ledger: **0 matured SCORE events** at this run; four already-pending forecasts suppressed as duplicates. No calibration or prospective edge claim.
- Risk: paper-only, live trading disabled, theoretical exposure **0%**.
- Registered experiment `V5.5-OHLCV-001` is **PROPOSED_NOT_RUN**, not an implemented or validated model improvement.

## V5.5 verified scope

V5.5 adds prospective matured-ledger scoring against the zero, drift and momentum forecasts saved at issuance; p90/p99 and worst-decile error diagnostics; low-sample regime warnings; explicit 0% theoretical exposure/abstention; a structured audit; and an append-only experiment proposal register. The historical 2025-11-16–2026-11-15 holdout is explicitly **not globally unseen** because it was previously inspected under V5.3.1. It is continuity diagnostics only. The next OHLCV feature experiment is registered as PROPOSED_NOT_RUN and is not represented as an achieved improvement.


## V5.5.1 — target timing correction

The daily research workflow is scheduled for 16:00 UTC. Since the next daily open `Open[t+1]` occurs at 00:00 UTC immediately after candle `t` closes, it has already passed by issuance. The production/executable research target therefore remains `log(Open[t+h+2]/Open[t+2])`, with one complete daily bar reserved for operational latency. The theoretical h+1 target is supported only as an explicitly non-executable diagnostic. Research and prospective ledger use the same target helper. Historical holdout rows are reported separately from matured prospective ledger SCORE events.


## V5.6.0 — permanent pre-report audit and ledger scoring correction

- Every daily run performs a mandatory audit **before** writing `run_report.json`: raw-object SHA-256/size, expected Binance monthly/daily archive completeness, Bitstamp page reconciliation, target timing, holdout governance, ledger integrity, benchmark status and risk fail-safe.
- A six-lens deep review rotates by UTC run-start second (data provenance; execution timing; ledger; statistics; risk/economics; efficiency/operations), so same-day reruns can inspect a different domain. The full baseline suite still runs every time. Reports also separate FACT/INTERPRETATION/HYPOTHESIS/FORECAST and include a dated 1/7/30-session price snapshot, pending point forecasts, the principal evidence limit and one next experiment.
- Critical audit failure changes report status to BLOCKED and enforces paper-only risk with 0% theoretical exposure.
- Full audit findings and historical outlier analysis: [permanent pre-report audit](docs/permanent-pre-report-audit-2026-11-17.md).
- Critical ledger defect fixed: Ridge forecasts are now serialized as scalar floats. The scorer also reads legacy one-element array strings already in the append-only ledger, so the first matured legacy forecast will not crash scoring. Historical records are not rewritten.
- Raw review of 2022-11-08 found close/open price corroboration between Binance and Bitstamp, but a 63.20x base-volume ratio. Venue-specific volume is not interchangeable; Coinbase/Kraken run windows do not cover the event date, so historical independent volume verification remains open.
- New tests cover the scalar serialization/scoring defect, archive completeness, raw hash integrity, Bitstamp overlap reconciliation and the outlier cross-check.
- Zero-return champion unchanged; Ridge unpromoted; probabilities disabled; Risk Overlay v1.1 paper-only; exposure 0%.

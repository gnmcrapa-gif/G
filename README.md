# BTC Quant Desk

Research-only BTC quantitative research project. This repository is not an execution engine, auto-trader, or personalized investment advice.

## Current verified status — 2026-11-16

- Protocol: **V5.4** (research upgrade; previous holdout preserved).
- Latest complete GitHub Actions run: **daily-research #42 — SUCCESS**.
- Research state: **COMPLETE_NOT_PROMOTED**. The data pipeline, QA, cross-checks, holdout evaluation, forecast ledger, and repository persistence all completed.
- Champion: zero-return baseline. Ridge remains a challenger and is **not promoted**.
- No calibrated probabilities, no trading orders, and no automatic position sizing.
- Risk Overlay v1.1 remains paper-only; when QA fails or predictive edge is not demonstrated, theoretical exposure is 0%.

### Persisted market data

The public repository currently contains 132 raw source objects (864,570 bytes), their manifest, SHA-256 hashes, retrieval timestamps, parser/schema versions, source grades, and provider-terms caveats. V5.4 adds explicit UTC-offset enforcement and blocks data more than one UTC day behind the current date.

| Source | Quote | Daily rows | Range UTC | Grade | QA |
|---|---|---:|---|---|---|
| Binance BTCUSDT | USDT | 3,378 | 2017-08-17 – 2026-11-15 | A | PASS |
| Bitstamp BTC/USD | USD | 3,650 | 2016-11-18 – 2026-11-15 | A | PASS |
| Coinbase BTC-USD | USD | 300 | 2026-01-20 – 2026-11-15 | B | PASS |
| Kraken XBT/USD | USD | 720 | 2024-11-26 – 2026-11-15 | B | PASS |

All dates are UTC candle-open timestamps; the last complete candle is 2026-11-15. Bitstamp pagination overlapped by 349 rows; the overlap is explicitly counted in the manifest and removed before QA. The canonical QA series has no duplicates or daily gaps. USDT/USD quote basis is not FX-adjusted; venues remain separate.

Provider terms apply to public endpoints/archives; no separate legal licensing review is claimed.

### Latest out-of-sample evaluation

Final holdout: **2025-11-16 through 2026-11-15 UTC**, untouched by training or tuning. Target horizons: 1, 3, 7, 30 days. The evaluation uses a one-daily-bar operational latency buffer so ledger entries are genuinely in the future at issue time. Ridge alpha is now selected across three purged, expanding chronological validation folds; the final holdout remains untouched. The report also includes Newey-West HAC paired absolute-loss comparisons (lag h-1 for overlapping targets), Holm family-wise multiple-testing correction, and ex-ante bull/bear/range diagnostics.

MAE is in **log-return units**, not percent. The historical metrics below are the V5.3.1 baseline and must not be represented as V5.4 rerun results until the V5.4 pipeline completes.

| Horizon | OOS n | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE |
|---:|---:|---:|---:|---:|---:|
| 1d | 362 | 0.015894 | 0.015958 | 0.027292 | 0.015956 |
| 3d | 360 | 0.028470 | 0.028681 | 0.049023 | 0.028752 |
| 7d | 356 | 0.042261 | 0.043085 | 0.076872 | 0.043009 |
| 30d | 333 | 0.101414 | 0.102499 | 0.185213 | 0.103350 |

Zero-return has the lowest MAE at every horizon. Ridge therefore remains unpromoted. Directional accuracy for the zero-return baseline is reported as not applicable, not as 0%. At least 200 matured OOS forecasts per horizon are available in this holdout, but this alone does not establish calibration or economic value.

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

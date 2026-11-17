# BTC Quant Desk

Research-only BTC quantitative research pipeline. This repository is not an execution engine, auto-trader, or personalized investment advice.

## Current verified production baseline — 2026-11-17

- Main-branch daily research run **#44155330178 — SUCCESS** on 2026-11-17 UTC.
- Production protocol at that run: **V5.5.1**. V5.6 is the proposed next protocol revision in this branch and is not considered production until its CI and post-merge live-data run pass.
- Run result: **COMPLETE_NOT_PROMOTED**.
- Champion: zero-return baseline, frozen. Drift and momentum are benchmarks. Ridge remains challenger only and is not promoted.
- Risk Overlay v1.1: paper-only; live trading disabled; theoretical exposure 0%.
- No calibrated probabilities, trading orders, or automatic position sizing.

## Verified data in the 2026-11-17 run

| Source | Instrument / quote | Daily rows | Range UTC | QA |
|---|---|---:|---|---|
| Binance spot | BTCUSDT / USDT | 3,379 | 2017-08-17 – 2026-11-16 | PASS |
| Bitstamp spot | BTC/USD / USD | 3,650 | 2016-11-19 – 2026-11-16 | PASS |
| Coinbase Exchange | BTC-USD / USD | 300 | 2026-01-21 – 2026-11-16 | PASS |
| Kraken | XBT/USD / USD | 720 | 2024-11-27 – 2026-11-16 | PASS |

All timestamps are UTC daily candle-open timestamps. Both primary venues have over five years of history, no duplicate timestamps or daily gaps, and the latest completed candle is 2026-11-16. Binance and Bitstamp are distinct datasets; USDT and USD are not FX-adjusted or merged. Coinbase/Kraken recent cross-checks passed. Raw source objects and their URLs, retrieval times, byte sizes, SHA-256 hashes, parser/schema metadata and page-overlap accounting are persisted in `data/raw/` and `reports/latest/data_manifest.json`.

### Data-quality findings

- The earlier full-history robust volume z-scores (27.21 for Binance and 23.00 for Bitstamp) are withdrawn: a single full-sample median/MAD is not a reliable outlier baseline for non-stationary exchange volume across 9–10 years.
- V5.6 replaces that statistic with a rolling 90-session median/MAD score, excluding the current session and requiring at least 60 prior observations. The new maximum and timestamp must be recomputed by the next V5.6 run; no replacement value is claimed yet.
- Binance largest absolute close-to-close log return in the V5.5.1 run: 0.5026 (log-return units), 2020-03-12 UTC.
- Binance largest intraday high-low range / open in the V5.5.1 run: 45.27%, 2020-03-13 UTC.
- Outlier diagnostics do not establish erroneous data. Venue-level volume is not expected to match.

## Historical continuity scorecard

The historical period 2025-11-17 through 2026-11-16 was previously inspected under earlier protocol versions. It is **not globally unseen** and is retained only as a historical continuity diagnostic. It is not prospective ledger evidence and cannot be used to promote a model.

MAE is in log-return units. Lower is better.

| Horizon | Rows | Zero MAE | Drift MAE | Momentum MAE | Ridge MAE | Ridge vs zero, Holm p |
|---:|---:|---:|---:|---:|---:|---:|
| 1 day | 362 | 0.015923 | 0.015988 | 0.027317 | 0.015989 | 1.000 |
| 3 days | 360 | 0.028545 | 0.028754 | 0.049102 | 0.028831 | 0.950 |
| 7 days | 356 | 0.042520 | 0.043340 | 0.076994 | 0.043273 | 0.950 |
| 30 days | 333 | 0.101881 | 0.102956 | 0.185131 | 0.103926 | 1.000 |

Zero-return has the lowest MAE at all four horizons. Ridge is worse than zero on all four aggregate MAE comparisons and no paired comparison rejects after Holm adjustment at 5%. The historical holdout is not evidence of prospective edge. Regime metrics remain descriptive; small slices are low-N.

## Prospective ledger

`ledger/forecast_ledger.csv` is append-only. In the 2026-11-17 production run, the ledger had 16 existing events, no new score events and no matured prospective forecast observations by horizon. Four duplicate pending forecasts were suppressed. Therefore the prospective sample gate is unmet and probability calibration is prohibited. Historical continuity rows do not count toward the 200 matured forecast minimum.

## Protocol and review gates

- **V5.5.1 (main production baseline):** corrected target/execution timing. The daily run executes at 16:00 UTC; `Open[t+1]` has already passed, so the production target is `log(Open[t+h+2]/Open[t+2])`. The h+1 target is theoretical, not executable at scheduled issuance.
- **V5.6 (proposed in this branch):** mandatory executable pre-report review gate, raw-object hash/size verification, Binance monthly/daily archive completeness, Bitstamp pagination reconciliation, cross-venue anomaly-event review, last-closed-candle snapshot, runtime diagnostics, and rotating adversarial review cycles. Any blocking failure forces BLOCKED and 0% theoretical exposure before report serialization. New ledger events are staged in memory and appended only after the pre-report gate passes; PR runs are read-only and skip persistent ledger writes.

See [Protocol V5.6](docs/protocol-v5.6.md), [Protocol V5.5](docs/protocol-v5.5.md), and [target/execution timing audit](docs/target-alignment-audit-2026-11-17.md).

## Research safeguards

1. Separate FACT, INTERPRETATION, HYPOTHESIS and FORECAST.
2. Never claim acquisition, parsing, QA, training, backtest, validation or persistence unless evidenced in the current run.
3. Preserve raw data, provenance, hashes, parser/schema versions and immutable forecast events.
4. Keep venue and quote currencies separate.
5. Use point-in-time features, chronological splits, purge/embargo and validation-only tuning.
6. Never reuse the historical continuity holdout for promotion.
7. Compare zero-return, drift and momentum benchmarks before considering challengers.
8. Statistical changes remain isolated challengers; the champion is frozen.
9. Require at least 200 matured prospective forecasts per horizon plus a separate calibration study before any probability claim.
10. No cost-adjusted strategy PnL is claimed until fees, spread, slippage, funding, turnover and drawdown are tested.
11. Stale data, QA failure or failed pre-report review means exposure 0%.
12. No auto-trading, order placement or live position sizing.

## Reproduction

Install development dependencies and run:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests scripts
python scripts/run_research.py
```

The daily GitHub Actions workflow runs at 16:00 UTC and stores raw data, manifests, reports and the append-only ledger on main. Pull-request runs validate code but do not mutate the production ledger or raw-data archive.

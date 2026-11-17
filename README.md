# BTC Quant Desk

Research-only BTC quantitative research pipeline. This repository is not an execution engine, auto-trader, or personalized investment advice.

## Current verified production baseline — 2026-11-17

- Main-branch V5.6 daily research run **#44180291352 — SUCCESS** (workflow event: push after merge).
- Code commit: `67d20c1dc83ee821e6328dfabee94b5f7ab8a9f3`; evidence/persistence commit: `e96af95194e4a2798852c2fdfc2109c7806f4a13`.
- Run result: **COMPLETE_NOT_PROMOTED**; the pre-report gate passed all seven review cycles.
- Champion: zero-return baseline, frozen. Drift and momentum are benchmarks. Ridge remains challenger only and is not promoted.
- Risk Overlay v1.1: paper-only; live trading disabled; theoretical exposure 0%.
- No calibrated probabilities, trading orders, or automatic position sizing.

## Verified data in the 2026-11-17 V5.6 run

| Source | Instrument / quote | Daily rows | Range UTC | QA |
|---|---|---:|---|---|
| Binance spot | BTCUSDT / USDT | 3,379 | 2017-08-17 – 2026-11-16 | PASS |
| Bitstamp spot | BTC/USD / USD | 3,650 | 2016-11-19 – 2026-11-16 | PASS |
| Coinbase Exchange | BTC-USD / USD | 300 | 2026-01-21 – 2026-11-16 | PASS |
| Kraken | XBT/USD / USD | 720 | 2024-11-27 – 2026-11-16 | PASS |

All timestamps are UTC daily candle-open timestamps. Both primary venues have over five years of history, no duplicate timestamps or daily gaps, and the latest completed candle is 2026-11-16. Binance and Bitstamp are distinct datasets; USDT and USD are not FX-adjusted or merged. Coinbase/Kraken recent cross-checks passed. The run downloaded 133 raw objects; all 133 object byte sizes and SHA-256 values matched the manifest in the uploaded diagnostic artifact. Raw source objects and their URLs, retrieval times, byte sizes, SHA-256 hashes, parser/schema metadata and page-overlap accounting are persisted in `data/raw/` and `reports/latest/data_manifest.json`.

### Data-quality findings

- Volume outliers use a rolling 90-session median/MAD baseline, excluding the current session and requiring at least 60 prior observations. Binance maximum robust score: 16.3063 on 2017-12-22 UTC. Bitstamp maximum: 18.4912 on 2022-05-12 UTC. These are diagnostics, not automatic data rejection.
- Binance largest absolute close-to-close log return: 0.502607 (log-return units), 2020-03-12 UTC.
- Binance largest intraday high-low range / open: 45.2680%, 2020-03-13 UTC.
- Venue-level volume is not expected to match. USD and USDT remain separate.

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

`ledger/forecast_ledger.csv` is append-only. In the 2026-11-17 V5.6 production run, the ledger contained 16 unique events, including 4 invalidations and 8 active pending forecasts. No score events were created and no prospective forecast had matured; four same-signal/same-version pending forecasts were correctly suppressed as duplicates. The prospective sample gate is unmet and probability calibration is prohibited. Historical continuity rows do not count toward the 200 matured forecast minimum.

Ledger deduplication is version-aware: a second run cannot duplicate a pending forecast for the same signal, horizon and model version, while a genuinely new model version may issue a separate forecast. Prospective metrics are reported separately by model version and are never pooled across versions.

## Protocol and review gates

- **V5.6 (main production protocol):** corrected target/execution timing plus mandatory executable pre-report review gate, raw-object hash/size verification, Binance monthly/daily archive completeness, Bitstamp pagination reconciliation, cross-venue anomaly-event review, last-closed-candle snapshot, runtime diagnostics, and seven rotating adversarial review cycles. Any blocking failure forces BLOCKED and 0% theoretical exposure before report serialization. New ledger events are staged in memory and appended only after the pre-report gate passes; PR runs are read-only and skip persistent ledger writes.

See [Protocol V5.6](docs/protocol-v5.6.md), [Changelog](CHANGELOG.md), [Protocol V5.5](docs/protocol-v5.5.md), and [target/execution timing audit](docs/target-alignment-audit-2026-11-17.md).

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

## Supplemental market context — implementation status

The V5.6 extension is adding timestamped public feeds for live last-trade spot snapshots, Binance/Bybit derivatives, Deribit options, US spot ETF flows and FRED macro/US indices. The daily report will show the actual observation date, retrieval time, quote/unit, source, freshness and any provider delay, plus headline timestamps and source domains. These context feeds do **not** train the current price-only Ridge challenger and do not alter the frozen zero-return champion.

Known source limits are explicit:
- Binance historical open-interest statistics and taker buy/sell ratio endpoints expose only about the latest 30 days; they are not long-history series.
- Deribit option open interest is denominated in BTC for options and delayed by 8 hours. Public open interest cannot reveal dealer positioning or the sign of dealer gamma.
- The public ETF dataset covers US spot Bitcoin ETFs, not global ETPs, and may lag issuer reporting.
- Exchange reserves/netflows require verified wallet labels; raw transfers are not exchange flows.
- A complete market-wide liquidation series, spot/futures CVD, global ETP flows and verified geopolitical/regulatory event feed are not claimed unless a source is actually acquired and QA-checked.
- FRED macro observations retain their native publication/observation dates; monthly and weekly series are not treated as real-time.

The report's coverage matrix distinguishes PASS, PARTIAL, STALE, PROXY_ONLY, UNAVAILABLE, NOT_IMPLEMENTED and NOT_RUN. Missing optional feeds never block primary OHLCV research by themselves, but are never represented as present. See [Protocol V5.6](docs/protocol-v5.6.md).

## Reproduction

Install development dependencies and run:

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests scripts
python scripts/run_research.py
```

The daily GitHub Actions workflow runs at 16:00 UTC and stores raw data, manifests, reports and the append-only ledger on main. Pull-request runs validate code but do not mutate the production ledger or raw-data archive.

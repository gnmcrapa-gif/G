# BTC Quant Desk — Protocol V5.3.1

**Purpose:** reproducible quantitative research on BTC market behaviour. This is not an execution engine, auto-trader, or personalized investment advice.

## 1. Evidence discipline

Every statement must be labelled as one of:

- **FACT** — directly observed in a source or reproducible computation.
- **INTERPRETATION** — reasoned explanation of facts.
- **HYPOTHESIS** — falsifiable proposition not yet established.
- **FORECAST** — time-stamped prediction with a defined target, horizon, benchmark, and expiry.

Never report a data download, parser run, QA check, training, backtest, validation, or audit as completed unless it was actually executed in the current run against identified data. If acquisition fails, preserve the exact source, attempt, and error. Do not replace missing raw history with snippets, screenshots, or snapshots.

Every run compares newly observed data with prior benchmarks, matured forecasts, and previous decisions where evidence exists. Do not invent historical forecasts or retroactively populate the ledger.

## 2. Forecast ledger

Append-only. Each record must include:
- forecast ID and immutable emission timestamp (UTC);
- model/code version and data manifest/hash;
- target definition, horizon, forecast value/distribution;
- benchmark forecast;
- issue-time feature cutoff and regime label determined ex ante;
- maturity/expiry timestamp;
- realized outcome and scoring status, populated only after maturity;
- invalidation reason, if any.

Never overwrite a forecast. Corrections are new linked records with an audit reason.

## 3. Data sources and venue separation

Primary intended sources:
- Binance Vision BTCUSDT spot OHLCV;
- Bitstamp BTC/USD spot OHLCV as independent venue/quote cross-check;
- recent Coinbase and Kraken data for cross-checks.

Do not concatenate venues or quote currencies without explicit basis handling. Explore21 public CSVs may be considered only after downloadability, provenance, schema, and integrity are validated. Derivatives, ETF, on-chain, options, and macro series are optional and admitted only with downloadable history, timestamps, methodology, and publication-lag controls.

Target history: at least five years; longer history is desirable where reliable. A source's presence on a website does not establish that its raw history was acquired.

## 4. Data quality and provenance

For every source record URL, retrieval time (UTC), license/terms, venue, quote currency, first/last timestamp, row count, expected frequency, timezone, parser/version, file size, and SHA-256.

Validate:
- timestamp uniqueness and strict monotonicity;
- UTC normalization, DST handling, candle closure and frequency;
- OHLC invariants and positive prices;
- duplicates, missing bars, gaps, outliers, scale/unit errors;
- volume units and zero-vs-missing semantics;
- split/merge or symbol/contract changes where applicable;
- point-in-time availability and publication lag;
- lineage from each feature to source field and availability time.

Assign source grades A/B/C/D; D is excluded. Never forward-fill market bars. Training uses closed UTC candles only; incomplete candles may be used solely as clearly labelled live snapshots. A failed/stale QA gate blocks model validation.

## 5. Target and timing

For close index `t` and horizon `h ∈ {1,3,7,30}`:

`y[t,h] = log(Open[t+h+2] / Open[t+2])`

Signal is formed after close `t`; the feature cutoff is the close timestamp. Because the daily research job runs after the UTC session boundary, one complete daily bar is reserved for operational latency: entry is at `Open[t+2]`, exit is at `Open[t+h+2]`. The ledger must reject any forecast whose entry timestamp is not strictly later than its actual issue timestamp. This avoids backdating an entry to an open that has already passed. Features must be known at or before close `t`. No lookahead, leakage, or use of incomplete bars in historical training.

## 6. Benchmarks and models

Required benchmarks:
- zero-return;
- drift estimated only from training data;
- fixed momentum benchmark.

Ridge is a challenger, not champion by default. Historical reported MAE values are unverified until independently reproduced from raw data. A previous synthetic 200-path experiment is synthetic-only and is not evidence about BTC.

## 7. Evaluation

Use chronological walk-forward splits. Purge/embargo at least the maximum target horizon plus the one-bar execution-latency buffer at each boundary. Tune only on validation. Keep final holdout untouched and never use it for model selection.

Report by horizon and regime:
- MAE, RMSE, directional accuracy, rank IC where meaningful;
- calibration and uncertainty, residual drift and distribution;
- worst-decile and shock performance;
- temporal concentration, regime instability, data coverage;
- leakage/placebo checks and timestamp alignment;
- sensitivity to fees, spread, slippage, funding, borrow, and turnover.

Correct for multiple testing. Compare against simple baselines and zero-return. Do not infer predictive skill from in-sample fit or synthetic paths.

## 8. Promotion and abstention

No probabilistic forecast claims unless at least 200 matured out-of-sample forecasts exist per horizon and calibration is verified. Otherwise state: **“nessun vantaggio predittivo dimostrato”**.

Promote a challenger only when out-of-sample lift is robustly above zero and simple benchmarks, stable across regimes/time, economically material, and resilient to realistic costs with uncertainty reported. A failed/stale data gate means **non validabile** and theoretical overlay 0%.

Champion remains frozen. Technical corrections (parser, timestamp, units, duplicates, missingness, leakage) require documented evidence and tests. Statistical changes are separate challengers; change one hypothesis family at a time.

## 9. Economic strategy and risk

Only evaluate an economic strategy after forecast edge is validated. Include fees, spread, slippage, funding, borrow, turnover, exposure, Sharpe, Sortino, drawdown, tail loss, and 1x/2x/3x cost stress.

Risk Overlay v1.1 is paper trading only and frozen. It must never trigger orders or automatically increase exposure. No execution, no auto-trading, no automatic position sizing. If stale/QA failure: theoretical exposure 0%.

## 10. Required run report

Every report includes:
1. executive summary and evidence status;
2. acquisition attempts and source-level QA;
3. price, volume, multi-timeframe context and regime;
4. benchmark comparison for 24h/72h/7d/30d where data permit;
5. forecasts and matured ledger scores;
6. derivatives, ETF, flows, options, on-chain, macro only with provenance;
7. risk and abstention status;
8. changes and reproducibility details;
9. sources and timestamps with timezone for every market reading;
10. independent critical audit with PASS/WARN/FAIL/BLOCKED, severity, evidence, consequence, action;
11. three key drivers, main limitation, falsifying evidence;
12. final decision: champion / challenger / rollback / abstain.

## 11. Mandatory critical self-review

At every run ask:
- What is the weakest component?
- Which assumptions are fragile?
- Which features add no demonstrable value and should be removed?
- What single next experiment could falsify the current interpretation?
- What must not be changed yet?

Red-team the conclusion. Compare performance longitudinally only across genuinely comparable datasets, definitions, and evaluation windows. End with reliability assessment, three vulnerabilities, one next experiment, what not to modify, and the champion/challenger/rollback/abstain decision.
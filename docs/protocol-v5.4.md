# BTC Quant Desk Protocol V5.4

V5.4 is a controlled research-quality upgrade over V5.3.1. It does not promote a predictive model and does not alter the prior V5.3.1 final-holdout record.

## Data contract

- Source timestamps must explicitly include a zero UTC offset. Naive timestamps and non-UTC offsets are rejected rather than silently normalized.
- Only closed daily candles are accepted.
- The newest daily candle must be no more than one UTC calendar day old. The 16:00 UTC daily run expects yesterday's complete candle.
- Daily cadence, monotonicity, uniqueness, OHLC invariants, finite positive prices, and finite non-negative volume are mandatory.
- Venue and quote currency series remain separate.

## Forecast target and timing

For signal bar t and horizon h in {1, 3, 7, 30}:

`y[t,h] = log(Open[t+h+2] / Open[t+2])`

Features are available only through close t. Entry is Open[t+2] and expiry is Open[t+h+2]. The extra daily bar is an explicit operational latency buffer. A forecast is not issued if its entry timestamp is not strictly later than its actual issue timestamp.

## Validation

- Chronological final holdout remains fixed and untouched by training and tuning.
- Ridge alpha is selected only on three expanding chronological validation folds.
- Each fold's training labels must mature before that fold's first validation signal; the horizon-specific purge is enforced.
- Holdout predictions are scored against zero-return, training-drift, fixed-momentum, and Ridge.
- The report includes MAE, RMSE, mean error, directional accuracy where meaningful, ex-ante bull/bear/range slices, and paired absolute-loss tests versus zero and drift.
- Paired loss tests use Newey-West HAC standard errors with max lag h-1 to account for overlapping target returns. Raw asymptotic normal-approximation p-values are adjusted across all horizon/benchmark comparisons using Holm's step-down family-wise error correction. These are diagnostics, not proof or automatic promotion criteria.

## Promotion and risk

No model is promoted automatically. Ridge remains a challenger until it shows consistent out-of-sample lift, robust paired-loss evidence, regime stability, calibration, and cost-adjusted economic value on genuinely prospective data. At least 200 matured OOS observations per horizon is a minimum sample gate, not a guarantee of statistical power.

No calibrated probability claims, no order placement, and no live trading. Risk Overlay v1.1 remains paper-only. Stale data, QA failure, or insufficient evidence means abstention and theoretical exposure 0%.

## Automatic improvement controls

Only deterministic technical fixes with regression tests may be applied to the production path. Statistical changes remain challengers, are documented with falsifiable hypotheses and predeclared criteria, and never tune the final holdout. The append-only forecast ledger is never rewritten to erase historical events.

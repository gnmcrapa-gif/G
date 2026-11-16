# BTC Quant Desk Protocol V5.5

V5.5 is a research-governance and prospective-evaluation upgrade. It does not promote Ridge and does not modify or retune the historical benchmark record.

## Corrections to historical evidence

The 2025-11-16 through 2026-11-15 period was previously inspected under V5.3.1. Although V5.4's three-fold alpha selection excluded that period from fitting and tuning, the period is not globally unseen. From V5.5 onward it is labelled **historical continuity diagnostic only**. It must not be described as an independent fresh holdout or used to claim prospective edge.

## Prospective forecast evidence

- Only append-only ledger events of type SCORE are used for prospective scoring.
- Each SCORE must map to an existing FORECAST event; pending and invalidated forecasts are excluded.
- Forecasts are compared with zero-return, training-drift, and fixed-momentum predictions saved at issue time.
- MAE, RMSE, mean error, and directional accuracy are reported by horizon.
- The 200 matured observations per horizon gate is a minimum for considering probabilistic calibration, not proof of calibration or power.
- No probabilities are published until a separate calibration study (reliability curve, Brier/log score as appropriate, calibration uncertainty, and prospective sample sufficiency) is completed.

## Error-tail and regime diagnostics

The historical continuity scorecard now reports p90/p99 absolute error, worst-decile mean absolute error, and maximum absolute error for every model. Regime slices are descriptive; any regime with fewer than 30 observations is marked LOW_N. These diagnostics are not treated as inferential proof.

Paired loss differences use Newey-West HAC standard errors, normal-approximation 95% intervals and p-values, with max lag h-1 for overlapping targets. Holm adjustment is applied across the predeclared family of horizon/comparator tests. The asymptotic approximation remains a limitation.

## Audit and risk controls

Every run writes:
- component-level PASS/WARN/BLOCKED audit;
- weakest component and three material vulnerabilities;
- falsifying evidence and next pre-registered experiment;
- explicit no-promotion decision;
- paper-only risk overlay with theoretical exposure 0% while edge/economic value is unproven.

The challenger experiment register is append-only. V5.5 registers OHLCV-001 as a proposal only: normalized volume surprise and candle geometry are to be tested as an isolated challenger using prospective data. No result is claimed until the experiment is implemented, run, and independently evaluated.

## Frozen decisions

- Zero-return remains the reference champion.
- Ridge remains challenger only.
- No auto-trading, order placement, or automatic exposure increase.
- The historical holdout cannot be recycled for future promotion.
- Statistical changes require a new prospective evidence window and realistic 1x/2x/3x cost tests.

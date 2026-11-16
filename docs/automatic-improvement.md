# Automatic improvement and critical self-audit

This process is mandatory on every research run. V5.5 adds prospective-only ledger scorecards, explicit historical holdout reuse disclosure, tail-error diagnostics, and an append-only challenger register; V5.4 added three purged expanding validation folds, HAC-aware paired-loss diagnostics, ex-ante regime slices, explicit UTC timestamp enforcement, and a one-calendar-day maximum age for daily data. It is not permission for uncontrolled model mutation.

## Every run

1. Verify source freshness, provenance, schema, timestamp monotonicity, OHLCV invariants, gaps, duplicates, units, and coverage.
2. Compare the run with prior reproducible runs and matured forecast-ledger records. Never fabricate missing history.
3. Score only matured forecasts. Report MAE, RMSE, directional accuracy, bias, residual drift, regime slices, worst-decile/shock behaviour, temporal concentration, and uncertainty where sample size permits.
4. Run leakage/placebo checks and verify feature availability timestamps against the forecast cutoff.
5. Independently audit each component: PASS/WARN/FAIL/BLOCKED, severity, evidence, consequence, and remediation.
6. State the weakest component, fragile assumptions, three vulnerabilities, falsifying evidence, and one next experiment.
7. Record all proposed changes in a challenger experiment log. A change must have a falsifiable hypothesis, frozen data/split, one change family, and predeclared acceptance criteria.
8. Run tests and compare challenger to frozen champion and simple benchmarks. Do not tune the final holdout.
9. Promote only after robust OOS lift, at least 200 matured OOS forecasts per horizon for probabilistic claims, regime stability, calibration, economic materiality, and 1x/2x/3x cost robustness.
10. If data are stale, QA fails, or evidence is insufficient: abstain; theoretical risk overlay is 0%.

## Permitted automatic actions

- Fix deterministic parser/schema/timezone/unit/duplicate/missingness bugs only with a failing test, a documented cause, and passing regression tests.
- Add diagnostics and tests that do not alter the frozen champion.
- Run isolated challenger experiments.
- Revert a failed experimental branch or keep the champion unchanged.

## Prohibited automatic actions

- No auto-trading, order placement, or automatic exposure increase.
- No unreviewed promotion, hyperparameter search on holdout, retroactive forecast creation, or overwriting ledger entries.
- No claiming a backtest was run if data acquisition or execution failed.

## Required report conclusion

Reliability status; component audit; weakest component; three vulnerabilities; one next experiment; what must not change; champion/challenger/rollback/abstain decision.


## V5.5 additions

- Treat the 2025-11-16 to 2026-11-15 period as historical continuity diagnostics only because it was previously examined in V5.3.1.
- Score only matured SCORE events linked to valid FORECAST events in the append-only ledger; exclude pending and invalidated records.
- Report p90/p99, worst-decile and maximum absolute forecast errors; mark regime slices with fewer than 30 observations LOW_N.
- Include a machine-readable component audit, weakest component, vulnerabilities, falsifying evidence, risk abstention, and next experiment in every run report.
- Register the OHLCV volume-surprise/candle-geometry hypothesis as PROPOSED_NOT_RUN. Do not claim it improves the model before prospective validation.

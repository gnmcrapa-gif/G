# Automatic improvement and critical self-audit

This process is mandatory on every research run. It is not permission for uncontrolled model mutation.

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

# BTC Quant Desk

Research-only BTC quantitative research project. This repository is public; never commit credentials, personal data, exchange account exports, or licensed/raw datasets without explicit permission.

## Status (2026-11-15)

- Protocol baseline: V5.3, documented in `docs/protocol-v5.3.md`.
- Data acquisition: **not yet completed in this repository**. No raw market dataset is currently committed.
- Model validation: **not performed by this scaffold**. Historical metrics mentioned in prior discussions are provisional and must be reproduced from identified raw data before use.
- Champion: conservative zero-return benchmark pending reproducible raw-data replication. Ridge and other predictive challengers are not promoted.
- Risk Overlay v1.1: paper-only, frozen; stale data or failed QA means theoretical exposure 0%.
- Automation: daily report scheduled for 17:00 Europe/Rome in ChatGPT; this repository does not itself guarantee execution of that schedule.

## Research principles

1. Distinguish FACT, INTERPRETATION, HYPOTHESIS, and FORECAST.
2. Never claim acquisition, parsing, QA, training, backtesting, or validation unless executed and evidenced for that run.
3. Preserve source provenance, retrieval timestamps, hashes, schema versions, and immutable forecast records.
4. Use point-in-time features and chronological walk-forward evaluation with purge/embargo.
5. Keep the final holdout untouched. Tune on validation only.
6. Promote a challenger only after robust out-of-sample lift, calibration, regime stability, and cost sensitivity checks.
7. Abstain when data are stale, incomplete, or fail QA.

## Target definition

For close time index `t`, horizon `h ∈ {1,3,7,30}`:

`y[t,h] = log(Open[t+h+1] / Open[t+1])`

Features are available no later than close `t`; the hypothetical entry is next session open and exit is open after `h` sessions. All timestamps are UTC. No lookahead.

## Quick start

Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The current code is a validation-first scaffold, not a trading system. Data adapters must be implemented and tested against official downloadable raw files before any model run is considered valid.

## Repository map

- `docs/protocol-v5.3.md`: operating and audit protocol.
- `docs/data-contract.md`: source, timestamp, QA, and lineage contract.
- `config/project.toml`: frozen research defaults.
- `src/btc_quant/`: schema checks, target construction, metrics.
- `tests/`: deterministic unit tests.
- `ledger/forecast_ledger.csv`: append-only forecast ledger header; no fabricated historical rows.
- `reports/`: run reports (only evidence-backed reports belong here).

## Security and data policy

The repository is public. Use environment variables or a secret manager for credentials; do not store secrets in Git. Keep raw datasets outside Git unless licensing and size have been checked. Record source URLs and SHA-256 manifests for every acquired file.
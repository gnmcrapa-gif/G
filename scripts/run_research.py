from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import traceback
from datetime import UTC, datetime
from pathlib import Path

from btc_quant.audit import build_pre_report_review
from btc_quant.acquisition import (
    download_binance_daily,
    download_bitstamp_recent,
    download_coinbase_recent,
    download_kraken_recent,
    write_manifest,
)
from btc_quant.ledger import (
    append_events,
    generate_forecast_events,
    invalidate_late_forecasts,
    read_events,
    score_matured_events,
    summarize_scored_events,
)
from btc_quant.research import cross_check_venues, walk_forward
from btc_quant.validation import validate_ohlcv


def _safe_optional_acquisition(label, function, directory):
    try:
        frame, manifest = function(directory)
        qa = validate_ohlcv(frame)
        return frame, {**manifest, "qa": {"status": "PASS", **qa}, "status": "PASS"}
    except Exception as exc:  # noqa: BLE001 - record each independent source failure
        return None, {"source": label, "status": "FAIL",
                      "url": {"Coinbase": "https://api.exchange.coinbase.com/products/BTC-USD/candles", "Kraken": "https://api.kraken.com/0/public/OHLC"}.get(label),
                      "attempted_at_utc": datetime.now(UTC).isoformat(),
                      "error": f"{type(exc).__name__}: {exc}"}



def _append_challenger_proposal(path: Path) -> None:
    """Register the next falsifiable experiment once; never imply it has been run."""
    experiment_id = "V5.5-OHLCV-001"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            existing = {row.get("experiment_id") for row in csv.DictReader(handle)}
    if experiment_id in existing:
        return
    fields = [
        "experiment_id", "created_at_utc", "hypothesis", "change_family",
        "data_manifest_sha256", "split_definition", "acceptance_criteria",
        "result", "decision", "review_notes",
    ]
    row = {
        "experiment_id": experiment_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "hypothesis": (
            "Normalized volume surprise and candle geometry may add prospective "
            "forecast information beyond close-only price features."
        ),
        "change_family": "OHLCV feature engineering; isolated challenger only",
        "data_manifest_sha256": "",
        "split_definition": (
            "Prospective ledger only; do not reuse the V5.3.1/V5.4 historical "
            "continuity holdout for promotion."
        ),
        "acceptance_criteria": (
            "At least 200 matured observations per horizon; positive MAE lift "
            "versus zero-return and frozen price-only challenger; HAC/Holm evidence; "
            "stable regimes; positive net value after 1x/2x/3x realistic costs."
        ),
        "result": "PROPOSED_NOT_RUN",
        "decision": "NOT_PROMOTED",
        "review_notes": "Pre-registered hypothesis only; no feature/model result is claimed.",
    }
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(row)


def _build_audit(run: dict, prospective: dict) -> dict:
    counts = {
        horizon: details.get("n", 0)
        for horizon, details in prospective.get("by_horizon", {}).items()
    }
    weakest = (
        "Prospective forecast evidence: no horizon has yet met the 200 matured "
        "forecast minimum required even to consider probabilistic calibration."
        if not counts or any(value < 200 for value in counts.values())
        else "Economic validation: fees, spread, slippage, funding and strategy-level drawdown tests remain outstanding."
    )
    return {
        "reliability_status": run.get("status", "BLOCKED"),
        "component_audit": [
            {"component": "primary_data_and_QA", "status": next(
                (step.get("status") for step in run.get("steps", [])
                 if step.get("step") == "binance_acquisition_and_qa"), "BLOCKED")},
            {"component": "independent_Bitstamp_QA", "status": next(
                (step.get("status") for step in run.get("steps", [])
                 if step.get("step") == "bitstamp_acquisition_and_qa"), "BLOCKED")},
            {"component": "cross_venue_checks", "status": (
                "PASS" if run.get("cross_checks") and all(
                    item.get("status") == "PASS" for item in run["cross_checks"]
                ) else "WARN_OR_BLOCKED")},
            {"component": "historical_holdout", "status": "DIAGNOSTIC_ONLY_NOT_GLOBALLY_UNSEEN"},
            {"component": "prospective_ledger", "status": prospective.get("decision", "INSUFFICIENT_PROSPECTIVE_EVIDENCE")},
            {"component": "economic_strategy_validation", "status": "NOT_COMPLETED"},
        ],
        "weakest_component": weakest,
        "three_vulnerabilities": [
            "The historical 2025-11-16 to 2026-11-15 holdout was previously inspected under V5.3.1; it is not independent prospective evidence.",
            "The predictive feature set remains price-only; derivatives, ETF flows, order flow, macro and on-chain data are not integrated.",
            "No executable strategy backtest with fees, spread, slippage, funding, turnover and drawdown stress has been completed.",
        ],
        "falsifying_evidence": (
            "A prospective sample with >=200 matured forecasts per horizon that fails to beat "
            "the zero-return benchmark after multiple-testing control and realistic costs "
            "falsifies the proposed feature/model improvement."
        ),
        "next_priority_experiment": "V5.5-OHLCV-001: isolated volume-surprise and candle-geometry challenger; prospective ledger only.",
        "decision": "KEEP_ZERO_RETURN_CHAMPION; RIDGE_CHALLENGER_ONLY; NO_PROMOTION; ABSTAIN_FROM_LIVE_RISK",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--output-dir", default="reports/latest")
    parser.add_argument("--ledger", default="ledger/forecast_ledger.csv")
    parser.add_argument("--challenger-log", default="ledger/challenger_log.csv")
    parser.add_argument("--min-train-rows", type=int, default=1095)
    args = parser.parse_args()
    data_dir, output_dir, ledger_path = Path(args.data_dir), Path(args.output_dir), Path(args.ledger)
    output_dir.mkdir(parents=True, exist_ok=True)
    run = {"started_at_utc": datetime.now(UTC).isoformat(), "status": "BLOCKED",
           "protocol": "V5.6.0", "steps": [], "limitations": []}
    manifests = []
    binance = None
    bitstamp = None
    try:
        binance, binance_manifest = download_binance_daily(data_dir / "binance")
        manifests.append(binance_manifest)
        binance_qa = validate_ohlcv(binance)
        run["steps"].append({"step": "binance_acquisition_and_qa", "status": "PASS", "qa": binance_qa})
        bitstamp, bitstamp_manifest = download_bitstamp_recent(data_dir / "bitstamp")
        manifests.append(bitstamp_manifest)
        bitstamp_qa = validate_ohlcv(bitstamp)
        run["steps"].append({"step": "bitstamp_acquisition_and_qa", "status": "PASS", "qa": bitstamp_qa})
        optional = [
            ("Coinbase", download_coinbase_recent, data_dir / "coinbase"),
            ("Kraken", download_kraken_recent, data_dir / "kraken"),
        ]
        cross_checks = []
        for label, function, directory in optional:
            frame, record = _safe_optional_acquisition(label, function, directory)
            manifests.append(record)
            if frame is not None:
                cross_checks.append({"venue": label, **cross_check_venues(binance.tail(len(frame)), frame)})
            run["steps"].append({"step": f"{label.lower()}_recent_cross_check", **record})
        run["cross_checks"] = cross_checks
        manifest_path = output_dir / "data_manifest.json"
        write_manifest(manifests, manifest_path)
        # The model consumes Binance BTCUSDT only. Keep the forecast idempotency
        # hash tied to model inputs, not dynamic optional cross-check payloads.
        object_hashes = sorted(
            item["sha256"] for source in manifests if source.get("venue") == "Binance"
            for item in source.get("objects", []) if item.get("sha256")
        )
        manifest_sha256 = hashlib.sha256(json.dumps(object_hashes).encode()).hexdigest()
        predictions, scores = walk_forward(binance, min_train_rows=args.min_train_rows)
        counts = predictions.groupby("horizon").size().to_dict() if len(predictions) else {}
        run["historical_continuity_rows_by_horizon"] = {str(k): int(v) for k, v in counts.items()}
        run["historical_continuity_role"] = "diagnostic_only_not_prospective_ledger_maturity"
        run["probabilistic_claims_allowed"] = False
        predictions.to_csv(output_dir / "oos_predictions.csv", index=False)
        (output_dir / "scores.json").write_text(json.dumps(scores, indent=2), encoding="utf-8")
        previous_events = read_events(ledger_path)
        invalidation_events = invalidate_late_forecasts(previous_events)
        score_events = score_matured_events(previous_events + invalidation_events, binance)
        ridge_alpha_by_horizon = {
            int(horizon): float(details["selected_alpha"])
            for horizon, details in scores.get("validation_tuning", {}).items()
        }
        forecast_events = (
            generate_forecast_events(
                binance, manifest_sha256, os.environ.get("GITHUB_SHA", "local-uncommitted"),
                min_train_rows=args.min_train_rows,
                ridge_alpha_by_horizon=ridge_alpha_by_horizon,
            )
            if scores.get("status") == "SCORED_NOT_PROMOTED" else []
        )
        scored_ids = {
            row.get("forecast_id") for row in previous_events + score_events
            if row.get("event_type") == "SCORE"
        }
        invalidated_ids = {
            row.get("forecast_id") for row in previous_events + invalidation_events
            if row.get("event_type") == "INVALIDATION"
        }
        pending_keys = {
            (row.get("signal_timestamp_utc"), int(row.get("horizon")))
            for row in previous_events
            if row.get("event_type") == "FORECAST"
            and row.get("forecast_id") not in scored_ids | invalidated_ids
        }
        before_dedupe = len(forecast_events)
        forecast_events = [
            row for row in forecast_events
            if (row["signal_timestamp_utc"], int(row["horizon"])) not in pending_keys
        ]
        duplicates_suppressed = before_dedupe - len(forecast_events)
        appended = append_events(ledger_path, invalidation_events + score_events + forecast_events)
        all_ledger_events = previous_events + invalidation_events + score_events + forecast_events
        prospective_summary = summarize_scored_events(
            previous_events + invalidation_events + score_events
        )
        run["prospective_ledger_validation"] = prospective_summary
        run["ledger"] = {"invalidations_created": len(invalidation_events),
                         "score_events_created": len(score_events),
                         "forecast_events_created": len(forecast_events),
                         "duplicate_forecasts_suppressed": duplicates_suppressed,
                         "events_appended": appended, "existing_events_before_run": len(previous_events),
                         "total_events_after_run": len(all_ledger_events),
                         "append_only": True}
        run["steps"].append({"step": "walk_forward", "status": scores["status"],
                             "oos_rows": len(predictions), "scores": scores})
        required_pass = all(step["status"] == "PASS" for step in run["steps"]
                            if step["step"] in {"binance_acquisition_and_qa", "bitstamp_acquisition_and_qa"})
        # Coinbase/Kraken corroborate the primary venues; optional outages are disclosed, not blocking.
        run["status"] = ("COMPLETE_NOT_PROMOTED" if required_pass
                         and scores["status"] == "SCORED_NOT_PROMOTED" else "BLOCKED")
        run["limitations"].append("Ridge is challenger only; no automatic promotion.")
        run["limitations"].append("Calibration and >=200 matured OOS forecasts per horizon are required before probabilities.")
        run["limitations"].append("Regime slices are descriptive; no regime-specific inferential claim is made.")
        run["limitations"].append("The reused historical holdout is continuity diagnostics only, not independent prospective evidence.")
        run["limitations"].append("No cost-adjusted strategy PnL, funding, slippage or execution backtest is claimed.")
        run["limitations"].append("No calibrated probability or live trading claim is permitted.")
    except Exception as exc:  # noqa: BLE001 - write a durable failure report for diagnosis
        run["status"] = "BLOCKED"
        run["error"] = f"{type(exc).__name__}: {exc}"
        run["error_traceback"] = traceback.format_exc()
        run["limitations"].append("No model claim or positive exposure is permitted when acquisition, QA, or evaluation is blocked.")
        write_manifest(manifests, output_dir / "data_manifest.json")
    try:
        _append_challenger_proposal(Path(args.challenger_log))
        prospective = run.get("prospective_ledger_validation", {
            "decision": "INSUFFICIENT_PROSPECTIVE_EVIDENCE", "by_horizon": {}
        })
        run["risk"] = {
            "overlay_version": "1.1",
            "mode": "paper_only",
            "live_trading_enabled": False,
            "theoretical_exposure_pct": 0.0,
            "reason": "No predictive edge and cost-adjusted strategy value have been demonstrated; abstain.",
        }
        run["audit"] = _build_audit(run, prospective)
        # Mandatory review runs before run_report.json is serialized. It checks
        # source-object hashes, archive coverage, target timing, holdout hygiene,
        # ledger invariants, risk gates and a rotating deep-review lens.
        ledger_events = read_events(ledger_path)
        review = build_pre_report_review(
            run, manifests, binance, bitstamp, ledger_events,
            root=Path.cwd(), now=datetime.now(UTC),
        )
        run["pre_report_review"] = review
        if review["gate"] == "BLOCKED":
            run["status"] = "BLOCKED"
            run["risk"]["theoretical_exposure_pct"] = 0.0
            run["risk"]["reason"] = "Mandatory pre-report audit blocked; abstain."
        run["audit"]["pre_report_gate"] = review["gate"]
        run["audit"]["rotating_review_lens"] = review["rotating_review"]["lens"]
        run["audit"]["decision"] = (
            "KEEP_ZERO_RETURN_CHAMPION; RIDGE_CHALLENGER_ONLY; NO_PROMOTION; "
            "ABSTAIN_FROM_LIVE_RISK"
        )
    except Exception as audit_exc:  # noqa: BLE001 - an audit failure must block confidence
        run["status"] = "BLOCKED"
        run["audit_error"] = f"{type(audit_exc).__name__}: {audit_exc}"
        run["risk"] = {
            "overlay_version": "1.1", "mode": "paper_only",
            "live_trading_enabled": False, "theoretical_exposure_pct": 0.0,
            "reason": "Audit execution failed; fail-closed.",
        }
        run["pre_report_review"] = {
            "execution_order": "BEFORE_REPORT_SERIALIZATION",
            "gate": "BLOCKED",
            "error": run["audit_error"],
        }
    run["finished_at_utc"] = datetime.now(UTC).isoformat()
    (output_dir / "run_report.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps(run, indent=2))
    return 0 if run["status"].startswith("COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())

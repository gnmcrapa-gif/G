from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from btc_quant.acquisition import (
    download_binance_daily,
    download_bitstamp_recent,
    download_coinbase_recent,
    download_kraken_recent,
    write_manifest,
)
from btc_quant.audit import run_pre_report_review
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




def _market_snapshot(frame, venue: str, symbol: str, quote: str, retrieved_at: str) -> dict:
    """Describe the latest closed daily candle; never label it a live spot quote."""
    latest = frame.iloc[-1]
    previous = frame.iloc[-2] if len(frame) > 1 else None
    prior_volumes = frame.iloc[-31:-1]["volume"].astype(float)
    prior_30d_median_volume = float(prior_volumes.median()) if not prior_volumes.empty else None
    stamp = pd.Timestamp(latest["timestamp"]).tz_convert("UTC")
    return {
        "venue": venue, "symbol": symbol, "quote_currency": quote,
        "snapshot_type": "latest_closed_daily_candle_not_realtime_spot",
        "candle_open_timestamp_utc": stamp.isoformat(),
        "candle_close_timestamp_utc": (stamp + pd.Timedelta(days=1)).isoformat(),
        "retrieved_at_utc": retrieved_at,
        "open_quote_per_btc": float(latest["open"]),
        "high_quote_per_btc": float(latest["high"]),
        "low_quote_per_btc": float(latest["low"]),
        "close_quote_per_btc": float(latest["close"]),
        "volume_btc": float(latest["volume"]),
        "prior_30d_median_volume_btc": prior_30d_median_volume,
        "volume_vs_prior_30d_median": (
            float(latest["volume"]) / prior_30d_median_volume
            if prior_30d_median_volume and prior_30d_median_volume > 0 else None
        ),
        "intraday_range_pct": (
            (float(latest["high"]) - float(latest["low"])) / float(latest["open"]) * 100.0
        ),
        "prior_close_quote_per_btc": float(previous["close"]) if previous is not None else None,
        "close_change_1d_pct": (
            (float(latest["close"]) / float(previous["close"]) - 1.0) * 100.0
            if previous is not None else None
        ),
    }


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



def _build_report_sections(run: dict, scores: dict) -> tuple[dict, dict, dict]:
    metrics = scores.get("holdout_metrics", {})
    horizons = sorted(metrics, key=lambda value: int(value))
    zero_wins = [
        horizon for horizon in horizons
        if metrics[horizon].get("zero", {}).get("mae") is not None
        and all(metrics[horizon]["zero"]["mae"] <= block.get("mae", float("inf"))
                for model, block in metrics[horizon].items() if model != "zero")
    ]
    prospective = run.get("prospective_ledger_validation", {})
    by_horizon = prospective.get("by_horizon", {})
    matured = {str(h): int(by_horizon.get(str(h), {}).get("n", 0)) for h in (1, 3, 7, 30)}
    new_forecasts = int(run.get("ledger", {}).get("forecast_events_created", 0))
    scored_now = int(run.get("ledger", {}).get("score_events_created", 0))
    snapshots = run.get("market_snapshot", {}).get("venues", [])
    primary = next((item for item in snapshots if item.get("venue") == "Binance"), None)
    drivers = []
    if primary:
        source = "Binance spot BTCUSDT"
        stamp = primary.get("candle_open_timestamp_utc")
        for name, value, unit, window in (
            ("Variazione close-to-close", primary.get("close_change_1d_pct"), "%",
             "1 sessione giornaliera"),
            ("Ampiezza intraday high-low/open", primary.get("intraday_range_pct"), "%",
             "candela giornaliera"),
            ("Volume rispetto alla mediana precedente", primary.get("volume_vs_prior_30d_median"),
             "multiplo", "volume giornaliero / mediana 30 sessioni precedenti"),
        ):
            if value is not None:
                drivers.append({
                    "name": name, "value": value, "unit": unit, "window": window,
                    "timestamp_utc": stamp, "source": source, "qa_status": "PASS",
                    "interpretation": "Osservazione descrittiva; non attribuzione causale.",
                })
    taxonomy = {
        "FACT": [
            {
                "statement": f"{step.get('step')}: {step.get('status')}.",
                "evidence": step.get("qa", step.get("error", "stato registrato nel run report")),
            }
            for step in run.get("steps", [])
        ] + [
            {
                "statement": "Le metriche storiche sono diagnostiche di continuità, non prove prospettiche.",
                "evidence": {
                    "holdout_role": scores.get("holdout_role"),
                    "holdout_globally_unseen": scores.get("holdout_globally_unseen"),
                    "historical_rows_by_horizon": run.get("historical_continuity_rows_by_horizon", {}),
                },
            },
            {
                "statement": "Il ledger prospettico conteggia esclusivamente eventi SCORE maturati.",
                "evidence": {"matured_by_horizon": matured, "new_score_events": scored_now},
            },
        ],
        "INTERPRETATION": [
            {
                "statement": "Zero-return ha la MAE più bassa in tutti gli orizzonti storici confrontati."
                if len(zero_wins) == len(horizons) and horizons else
                "Il confronto storico non dimostra un vantaggio uniforme del challenger.",
                "horizons_where_zero_has_lowest_mae": zero_wins,
                "scope": "holdout storico già ispezionato; sola diagnostica di continuità",
            },
            {
                "statement": "Ridge resta challenger non promosso; nessuna conclusione economica è autorizzata.",
            },
        ],
        "HYPOTHESIS": [
            {
                "experiment_id": "V5.5-OHLCV-001",
                "statement": "Volume normalizzato e geometria delle candele potrebbero aggiungere informazione oltre le feature price-only.",
                "status": "PROPOSED_NOT_RUN",
                "evaluation_scope": "solo ledger prospettico; holdout storico escluso",
            },
        ],
        "FORECAST": {
            "new_point_forecasts_issued_this_run": new_forecasts,
            "new_forecasts_scored_this_run": scored_now,
            "matured_prospective_counts_by_horizon": matured,
            "calibrated_probabilities_published": False,
            "directional_alerts_published": False,
            "qualification": "Eventuali valori nel ledger sono point forecast sperimentali; non sono probabilità calibrate né segnali operativi.",
        },
    }
    economic = {
        "status": "BLOCKED_INSUFFICIENT_PROSPECTIVE_EVIDENCE",
        "matured_prospective_forecasts_by_horizon": matured,
        "minimum_required_per_horizon": 200,
        "historical_holdout_used_for_economic_promotion": False,
        "cost_adjusted_strategy_backtest_executed": False,
        "reason": (
            "Nessun campione prospettico maturo sufficiente; il periodo storico è già stato ispezionato. "
            "Non sono disponibili nel run una regola operativa approvata e serie storiche documentate "
            "di fee effettive, spread, slippage e funding per simulare PnL eseguibile."
        ),
        "required_inputs": [
            "almeno 200 forecast prospettici maturati per orizzonte",
            "regola di ingresso/uscita e sizing fissata ex ante",
            "fee schedule applicabile all'account/venue e relativo timestamp",
            "spread e slippage osservati o una sensibilità esplicitamente ipotetica",
            "funding solo per strumenti derivati, con serie e timestamp",
            "stress 1x/2x/3x costi, turnover, drawdown e confronto benchmark",
        ],
    }
    closing = {
        "observed_drivers": drivers,
        "principal_limit": (
            "Assenza di evidenza prospettica maturata e di validazione economica eseguibile; "
            "il holdout storico è solo diagnostico."
        ),
        "evidence_that_would_change_assessment": (
            "Un campione prospettico indipendente, almeno 200 osservazioni maturate per orizzonte, "
            "lift stabile contro zero-return/drift dopo HAC-Holm, calibrazione verificata e valore netto "
            "positivo dopo costi documentati e stress 1x/2x/3x."
        ),
        "single_next_priority_experiment": (
            "V5.5-OHLCV-001: challenger volume-surprise/candle-geometry, registrato prima del test "
            "e valutato esclusivamente sul ledger prospettico."
        ),
    }
    return taxonomy, economic, closing


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
    process_started = time.perf_counter()
    stage_started = process_started
    run = {"started_at_utc": datetime.now(UTC).isoformat(), "status": "BLOCKED",
           "protocol": "V5.6", "steps": [], "limitations": []}
    manifests = []
    binance = bitstamp = None
    scores = {}
    all_ledger_events = []
    pending_events = []
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
        run["performance"] = {"acquisition_and_qa_seconds": round(time.perf_counter() - stage_started, 3)}
        run["market_snapshot"] = {
            "as_of_utc": datetime.now(UTC).isoformat(),
            "warning": "These are last closed daily candles, not live spot quotes; USD and USDT are not converted or combined.",
            "venues": [
                _market_snapshot(binance, "Binance", "BTCUSDT", "USDT", binance_manifest["retrieved_at_utc"]),
                _market_snapshot(bitstamp, "Bitstamp", "BTC/USD", "USD", bitstamp_manifest["retrieved_at_utc"]),
            ],
        }
        manifest_path = output_dir / "data_manifest.json"
        write_manifest(manifests, manifest_path)
        # The model consumes Binance BTCUSDT only. Keep the forecast idempotency
        # hash tied to model inputs, not dynamic optional cross-check payloads.
        object_hashes = sorted(
            item["sha256"] for source in manifests if source.get("venue") == "Binance"
            for item in source.get("objects", []) if item.get("sha256")
        )
        manifest_sha256 = hashlib.sha256(json.dumps(object_hashes).encode()).hexdigest()
        research_started = time.perf_counter()
        predictions, scores = walk_forward(binance, min_train_rows=args.min_train_rows)
        run["performance"]["walk_forward_seconds"] = round(time.perf_counter() - research_started, 3)
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
        pending_events = invalidation_events + score_events + forecast_events
        all_ledger_events = previous_events + pending_events
        prospective_summary = summarize_scored_events(
            previous_events + invalidation_events + score_events
        )
        run["prospective_ledger_validation"] = prospective_summary
        run["ledger"] = {"invalidations_created": len(invalidation_events),
                         "score_events_created": len(score_events),
                         "forecast_events_created": len(forecast_events),
                         "duplicate_forecasts_suppressed": duplicates_suppressed,
                         "events_proposed": len(pending_events), "events_appended": 0,
                         "persistence_status": "PENDING_PRE_REPORT_REVIEW",
                         "existing_events_before_run": len(previous_events),
                         "total_events_proposed": len(all_ledger_events),
                         "total_events_after_run": len(previous_events),
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
    run.setdefault("performance", {})
    try:
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
        run["report_taxonomy"], run["economic_validation"], run["closing_assessment"] = (
            _build_report_sections(run, scores)
        )
        review_started = time.perf_counter()
        run["pre_report_review"] = run_pre_report_review(
            run, manifests, binance, bitstamp, all_ledger_events, scores,
            now=datetime.now(UTC), run_id=os.environ.get("GITHUB_RUN_ID",
            os.environ.get("GITHUB_RUN_ATTEMPT", run["started_at_utc"])),
        )
        run["performance"]["pre_report_review_seconds"] = round(time.perf_counter() - review_started, 3)
        if run["pre_report_review"]["status"] != "PASS":
            run["status"] = "BLOCKED"
            run["risk"] = {
                "overlay_version": "1.1", "mode": "paper_only",
                "live_trading_enabled": False, "theoretical_exposure_pct": 0.0,
                "reason": "Mandatory pre-report review failed; fail-closed abstention.",
            }
            run["audit"]["decision"] = "BLOCKED_BY_PRE_REPORT_REVIEW"
            if "ledger" in run:
                run["ledger"]["persistence_status"] = "SKIPPED_PRE_REPORT_REVIEW_FAILED"
        else:
            try:
                _append_challenger_proposal(Path(args.challenger_log))
                appended = append_events(ledger_path, pending_events)
                if "ledger" in run:
                    run["ledger"]["events_appended"] = appended
                    run["ledger"]["total_events_after_run"] = (
                        run["ledger"]["existing_events_before_run"] + appended
                    )
                    run["ledger"]["persistence_status"] = "PASS"
            except Exception as persistence_exc:  # noqa: BLE001 - persistence failure blocks the run
                run["status"] = "BLOCKED"
                run["persistence_error"] = f"{type(persistence_exc).__name__}: {persistence_exc}"
                if "ledger" in run:
                    run["ledger"]["persistence_status"] = "FAIL"
                run["risk"] = {
                    "overlay_version": "1.1", "mode": "paper_only",
                    "live_trading_enabled": False, "theoretical_exposure_pct": 0.0,
                    "reason": "Post-review ledger persistence failed; fail-closed abstention.",
                }
    except Exception as audit_exc:  # noqa: BLE001 - an audit failure must block confidence
        run["status"] = "BLOCKED"
        run["audit_error"] = f"{type(audit_exc).__name__}: {audit_exc}"
        run["risk"] = {
            "overlay_version": "1.1", "mode": "paper_only",
            "live_trading_enabled": False, "theoretical_exposure_pct": 0.0,
            "reason": "Audit failure; fail-closed abstention.",
        }
        run["pre_report_review"] = {
            "version": "pre-report-review-1.0",
            "executed_before_report_serialization": False,
            "status": "FAIL", "publication_gate": "BLOCKED",
            "blocking_failures": ["pre_report_review_exception"],
            "error": f"{type(audit_exc).__name__}: {audit_exc}",
        }
        run["status"] = "BLOCKED"
        if "ledger" in run:
            run["ledger"]["persistence_status"] = "SKIPPED_PRE_REPORT_REVIEW_EXCEPTION"
    run.setdefault("performance", {})["total_seconds_before_report"] = round(time.perf_counter() - process_started, 3)
    run["finished_at_utc"] = datetime.now(UTC).isoformat()
    (output_dir / "run_report.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps(run, indent=2))
    return 0 if run["status"].startswith("COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())

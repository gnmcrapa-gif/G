from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from btc_quant.acquisition import (
    download_binance_daily, download_bitstamp_recent, download_coinbase_recent,
    download_kraken_recent, write_manifest,
)
from btc_quant.ledger import append_events, generate_forecast_events, read_events, score_matured_events
from btc_quant.research import cross_check_venues, walk_forward
from btc_quant.validation import validate_ohlcv


def _safe_optional_acquisition(label, function, directory):
    try:
        frame, manifest = function(directory)
        qa = validate_ohlcv(frame)
        return frame, {**manifest, "qa": {"status": "PASS", **qa}, "status": "PASS"}
    except Exception as exc:  # noqa: BLE001 - record each independent source failure
        return None, {"source": label, "status": "FAIL",
                      "error": f"{type(exc).__name__}: {exc}", "retrieved_at_utc": datetime.now(UTC).isoformat()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--output-dir", default="reports/latest")
    parser.add_argument("--ledger", default="ledger/forecast_ledger.csv")
    parser.add_argument("--min-train-rows", type=int, default=1095)
    args = parser.parse_args()
    data_dir, output_dir, ledger_path = Path(args.data_dir), Path(args.output_dir), Path(args.ledger)
    output_dir.mkdir(parents=True, exist_ok=True)
    run = {"started_at_utc": datetime.now(UTC).isoformat(), "status": "BLOCKED",
           "protocol": "V5.3", "steps": [], "limitations": []}
    manifests = []
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
        manifest_path = output_dir / "data_manifest.json"
        write_manifest(manifests, manifest_path)
        object_hashes = sorted(item["sha256"] for source in manifests
                               for item in source.get("objects", []) if item.get("sha256"))
        manifest_sha256 = hashlib.sha256(json.dumps(object_hashes).encode()).hexdigest()
        predictions, scores = walk_forward(binance, min_train_rows=args.min_train_rows)
        counts = predictions.groupby("horizon").size().to_dict() if len(predictions) else {}
        run["matured_oos_counts_by_horizon"] = {str(k): int(v) for k, v in counts.items()}
        run["probabilistic_claims_allowed"] = False
        predictions.to_csv(output_dir / "oos_predictions.csv", index=False)
        (output_dir / "scores.json").write_text(json.dumps(scores, indent=2), encoding="utf-8")
        previous_events = read_events(ledger_path)
        score_events = score_matured_events(previous_events, binance)
        forecast_events = generate_forecast_events(
            binance, manifest_sha256, os.environ.get("GITHUB_SHA", "local-uncommitted"),
            min_train_rows=args.min_train_rows,
        )
        appended = append_events(ledger_path, score_events + forecast_events)
        run["ledger"] = {"score_events_created": len(score_events),
                         "forecast_events_created": len(forecast_events),
                         "events_appended": appended, "existing_events_before_run": len(previous_events),
                         "append_only": True}
        run["steps"].append({"step": "walk_forward", "status": scores["status"],
                             "oos_rows": len(predictions), "scores": scores})
        required_pass = all(step["status"] == "PASS" for step in run["steps"]
                            if step["step"] in {"binance_acquisition_and_qa", "bitstamp_acquisition_and_qa"})
        optional_status = all(step.get("status") == "PASS" for step in run["steps"]
                              if step["step"].endswith("_cross_check"))
        run["status"] = ("COMPLETE_NOT_PROMOTED" if required_pass and optional_status
                         and scores["status"] == "SCORED_NOT_PROMOTED" else "BLOCKED")
        run["limitations"].append("Ridge is challenger only; no automatic promotion.")
        run["limitations"].append("Calibration and >=200 matured OOS forecasts per horizon are required before probabilities.")
        run["limitations"].append("No regime-stratified significance, multiple-testing correction or cost-adjusted strategy backtest is claimed.")
    except Exception as exc:  # noqa: BLE001 - write a durable failure report for diagnosis
        run["status"] = "BLOCKED"
        run["error"] = f"{type(exc).__name__}: {exc}"
        run["limitations"].append("No model claim or positive exposure is permitted when acquisition, QA, or evaluation is blocked.")
        write_manifest(manifests, output_dir / "data_manifest.json")
    run["finished_at_utc"] = datetime.now(UTC).isoformat()
    (output_dir / "run_report.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps(run, indent=2))
    return 0 if run["status"].startswith("COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from btc_quant.acquisition import download_binance_daily, download_bitstamp_recent, write_manifest
from btc_quant.ledger import (
    append_events,
    generate_forecast_events,
    read_events,
    score_matured_events,
)
from btc_quant.research import cross_check_venues, walk_forward
from btc_quant.validation import validate_ohlcv


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
        binance, manifest = download_binance_daily(data_dir / "binance")
        manifests.append(manifest)
        qa = validate_ohlcv(binance)
        run["steps"].append({"step": "binance_acquisition_and_qa", "status": "PASS",
                             "qa": qa, "first": binance.timestamp.min().isoformat(),
                             "last": binance.timestamp.max().isoformat()})
        bitstamp, bs_manifest = download_bitstamp_recent(data_dir / "bitstamp")
        manifests.append(bs_manifest)
        bs_qa = validate_ohlcv(bitstamp)
        run["steps"].append({"step": "bitstamp_acquisition_and_qa", "status": "PASS", "qa": bs_qa})
        venue_check = cross_check_venues(binance, bitstamp)
        run["steps"].append({"step": "venue_cross_check", **venue_check})
        manifest_path = output_dir / "data_manifest.json"
        write_manifest(manifests, manifest_path)
        object_hashes = sorted(
            item["sha256"]
            for source in manifests
            for item in source.get("objects", [source])
            if item.get("sha256")
        )
        manifest_sha256 = hashlib.sha256(json.dumps(object_hashes).encode()).hexdigest()
        # Venue and quote currencies remain separate; Binance is the modelling series.
        predictions, scores = walk_forward(binance, min_train_rows=args.min_train_rows)
        counts = predictions.groupby("horizon").size().to_dict() if len(predictions) else {}
        run["matured_oos_counts_by_horizon"] = {str(k): int(v) for k, v in counts.items()}
        run["probabilistic_claims_allowed"] = False  # Calibration is not implemented/validated yet.
        predictions.to_csv(output_dir / "oos_predictions.csv", index=False)
        (output_dir / "scores.json").write_text(json.dumps(scores, indent=2), encoding="utf-8")

        previous_events = read_events(ledger_path)
        score_events = score_matured_events(previous_events, binance)
        forecast_events = generate_forecast_events(
            binance, manifest_sha256, os.environ.get("GITHUB_SHA", "local-uncommitted"),
            min_train_rows=args.min_train_rows,
        )
        ledger_appended = append_events(ledger_path, score_events + forecast_events)
        run["ledger"] = {
            "score_events_created": len(score_events),
            "forecast_events_created": len(forecast_events),
            "events_appended": ledger_appended,
            "existing_events_before_run": len(previous_events),
            "append_only": True,
        }
        run["steps"].append({"step": "walk_forward", "status": scores["status"],
                             "oos_rows": len(predictions), "scores": scores})
        run["status"] = "COMPLETE_NOT_PROMOTED" if scores["status"] == "SCORED_NOT_PROMOTED" else "BLOCKED"
        run["limitations"].append("Ridge is a challenger only. Calibration, regime-stratified significance, multiple-testing correction, cost-adjusted strategy backtest, and independent Python replication remain incomplete.")
        run["limitations"].append("Probabilistic forecast claims are disabled until calibration is independently validated.")
    except Exception as exc:  # noqa: BLE001 - record the failure in the run report
        run["status"] = "BLOCKED"
        run["error"] = f"{type(exc).__name__}: {exc}"
        run["limitations"].append("No model claim or positive exposure is permitted when acquisition, QA, or evaluation is blocked.")
    run["finished_at_utc"] = datetime.now(UTC).isoformat()
    (output_dir / "run_report.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps(run, indent=2))
    return 0 if run["status"].startswith("COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())

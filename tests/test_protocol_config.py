import tomllib
from pathlib import Path


def test_project_config_matches_production_protocol_v56():
    config = tomllib.loads((Path(__file__).parents[1] / "config" / "project.toml").read_text())
    assert config["project"]["protocol"] == "V5.6"
    assert config["project"]["research_schedule_utc"] == "16:00"
    assert config["project"]["execution_entry_lag_sessions"] == 2
    assert config["project"]["target"] == "log(open[t+h+2] / open[t+2])"
    assert config["validation"]["historical_holdout_globally_unseen"] is False
    assert config["risk"]["auto_trading"] is False
    assert config["risk"]["automatic_exposure_increase"] is False

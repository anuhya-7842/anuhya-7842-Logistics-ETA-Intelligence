import json
from pathlib import Path

import pandas as pd

from src.config import DATA_DIR


def load_anomalies():
    with open(
        DATA_DIR / "anomaly_records.json",
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def get_scenario(anomalies, scenario_id):
    return next(
        item
        for item in anomalies
        if item["scenario_id"] == scenario_id
    )


def test_ingestion_time_before_event_time_is_detected():
    anomalies = load_anomalies()
    scenario = get_scenario(anomalies, "ANOM-001")

    record = scenario["record"]

    event_time = pd.to_datetime(record["event_time"], utc=True)
    ingestion_time = pd.to_datetime(
        record["ingestion_time"],
        utc=True
    )

    assert ingestion_time < event_time


def test_impossible_route_order_is_detected():
    anomalies = load_anomalies()
    scenario = get_scenario(anomalies, "ANOM-002")

    records = scenario["records"]

    sequences = [
        record["leg_sequence"]
        for record in records
    ]

    assert sequences != sorted(sequences)


def test_future_event_is_after_prediction_time():
    anomalies = load_anomalies()
    scenario = get_scenario(anomalies, "ANOM-003")

    prediction_time = pd.to_datetime(
        scenario["prediction_as_of"],
        utc=True
    )

    event_time = pd.to_datetime(
        scenario["future_event"]["event_time"],
        utc=True
    )

    assert event_time > prediction_time


def test_delivered_shipment_status_conflict_is_detected():
    anomalies = load_anomalies()
    scenario = get_scenario(anomalies, "ANOM-004")

    assert scenario["delivered_event_present"] is True
    assert scenario["baseline_status"] in {
        "DELIVERED",
        "DELAYED"
    }
    assert scenario["anomalous_status"] == "IN_TRANSIT"
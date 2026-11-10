import pandas as pd

from src.config import DATA_DIR


def load_snapshots():
    return pd.read_csv(DATA_DIR / "eta_snapshots.csv")


def test_snapshot_dataset_exists_and_has_records():
    snapshots = load_snapshots()

    assert len(snapshots) > 0
    assert snapshots["shipment_id"].notna().all()


def test_snapshot_shipment_time_pairs_are_unique():
    snapshots = load_snapshots()

    assert not snapshots.duplicated(
        ["shipment_id", "prediction_time"]
    ).any()


def test_missing_eta_values_have_exception_status():
    snapshots = load_snapshots()

    missing = snapshots[snapshots["predicted_eta"].isna()]

    assert (
        missing["status"] == "POTENTIALLY_OVERDUE_NO_SCAN"
    ).all()

    assert (
        missing["delay_reason"] == "MISSING_ARRIVAL_SCAN"
    ).all()


def test_valid_eta_predictions_are_not_in_the_past():
    snapshots = load_snapshots()

    valid = snapshots[
        snapshots["predicted_eta"].notna()
        & (snapshots["status"] != "DELIVERED")
    ].copy()

    prediction_times = pd.to_datetime(
        valid["prediction_time"],
        utc=True,
        format="ISO8601"
    )

    predicted_times = pd.to_datetime(
        valid["predicted_eta"],
        utc=True,
        format="ISO8601"
    )

    assert (predicted_times >= prediction_times).all()


def test_delivery_snapshots_match_delivery_scan_times():
    snapshots = load_snapshots()

    events = pd.read_csv(DATA_DIR / "tracking_events.csv")

    queues = pd.read_csv(DATA_DIR / "facility_queues.csv")

    cutoff_time = pd.to_datetime(
        queues["snapshot_time"],
        utc=True,
        format="ISO8601"
    ).max()

    events["event_time"] = pd.to_datetime(
        events["event_time"],
        utc=True,
        format="ISO8601"
    )

    events["ingestion_time"] = pd.to_datetime(
        events["ingestion_time"],
        utc=True,
        format="ISO8601"
    )

    delivery_events = events[
        (events["event_type"] == "DELIVERED")
        & (events["event_status"] == "VALID")
        & (events["event_time"] <= cutoff_time)
        & (events["ingestion_time"] <= cutoff_time)
    ].copy()

    delivered_snapshots = snapshots[
        snapshots["status"] == "DELIVERED"
    ].copy()

    delivered_snapshots["prediction_time"] = pd.to_datetime(
        delivered_snapshots["prediction_time"],
        utc=True,
        format="ISO8601"
    )

    delivered_snapshots["predicted_eta"] = pd.to_datetime(
        delivered_snapshots["predicted_eta"],
        utc=True,
        format="ISO8601"
    )

    matched = delivery_events.merge(
        delivered_snapshots,
        left_on=["shipment_id", "ingestion_time"],
        right_on=["shipment_id", "prediction_time"],
        how="inner"
    )

    assert len(matched) > 0

    assert (
        matched["predicted_eta"] == matched["event_time"]
    ).all()


def test_snapshot_times_do_not_exceed_queue_data_cutoff():
    snapshots = load_snapshots()

    queues = pd.read_csv(DATA_DIR / "facility_queues.csv")

    latest_queue_time = pd.to_datetime(
        queues["snapshot_time"],
        utc=True,
        format="ISO8601"
    ).max()

    latest_prediction_time = pd.to_datetime(
        snapshots["prediction_time"],
        utc=True,
        format="ISO8601"
    ).max()

    assert latest_prediction_time <= latest_queue_time


def test_missing_base_travel_and_eta_values_are_consistent():
    snapshots = load_snapshots()

    assert (
        snapshots["base_travel_minutes"].isna()
        == snapshots["predicted_eta"].isna()
    ).all()

import pandas as pd

from src.config import DATA_DIR


def validate_primary_keys(df, column, table_name):
    if df[column].isnull().any():
        raise ValueError(f"{table_name}: Null primary keys found")

    if df[column].duplicated().any():
        raise ValueError(f"{table_name}: Duplicate primary keys found")

    print(f"PASS: {table_name} primary keys are valid")


def validate_master_data():
    files = {
        "carriers": "carrier_id",
        "facilities": "facility_id",
        "routes": "route_id",
        "service_levels": "service_level_id"
    }

    datasets = {}

    for table, primary_key in files.items():
        filepath = DATA_DIR / f"{table}.csv"

        if not filepath.exists():
            raise FileNotFoundError(f"Missing file: {filepath}")

        df = pd.read_csv(filepath)

        validate_primary_keys(df, primary_key, table)

        datasets[table] = df

    # Validate route facility references
    facility_ids = set(datasets["facilities"]["facility_id"])

    for column in ["origin_facility_id", "destination_facility_id"]:
        invalid = set(datasets["routes"][column]) - facility_ids

        if invalid:
            raise ValueError(f"Invalid facility references in routes: {invalid}")

    print("PASS: Route facility foreign keys are valid")

    # Validate carrier status
    valid_statuses = {"ACTIVE", "INACTIVE"}

    if not set(datasets["carriers"]["operating_status"]).issubset(valid_statuses):
        raise ValueError("Invalid carrier operating status")

    print("PASS: Carrier statuses are valid")

    print("\nAll master data validations passed!")

def validate_shipments():
    print("\nValidating shipment data...")

    shipments = pd.read_csv(DATA_DIR / "shipments.csv")
    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    routes = pd.read_csv(DATA_DIR / "routes.csv")
    carriers = pd.read_csv(DATA_DIR / "carriers.csv")
    facilities = pd.read_csv(DATA_DIR / "facilities.csv")
    services = pd.read_csv(DATA_DIR / "service_levels.csv")

    # Primary key validation
    validate_primary_keys(
        shipments, "shipment_id", "shipments"
    )

    validate_primary_keys(
        legs, "leg_id", "shipment_legs"
    )

    # Foreign key validation
    shipment_ids = set(shipments["shipment_id"])
    route_ids = set(routes["route_id"])
    carrier_ids = set(carriers["carrier_id"])
    facility_ids = set(facilities["facility_id"])
    service_ids = set(services["service_level_id"])

    assert set(legs["shipment_id"]).issubset(shipment_ids)
    assert set(legs["route_id"]).issubset(route_ids)
    assert set(legs["carrier_id"]).issubset(carrier_ids)

    assert set(shipments["carrier_id"]).issubset(carrier_ids)
    assert set(shipments["service_level_id"]).issubset(service_ids)

    for column in [
        "origin_facility_id",
        "destination_facility_id"
    ]:
        assert set(shipments[column]).issubset(facility_ids)
        assert set(legs[column]).issubset(facility_ids)

    print("PASS: All shipment foreign keys are valid")

    # Every shipment must have at least two legs
    leg_counts = legs.groupby("shipment_id").size()

    assert (leg_counts >= 2).all()
    assert set(leg_counts.index) == shipment_ids

    print("PASS: Every shipment has multiple legs")

    # Validate route-to-leg facility relationships
    route_lookup = routes.set_index("route_id")

    for leg in legs.itertuples(index=False):
        route = route_lookup.loc[leg.route_id]

        assert route["origin_facility_id"] == leg.origin_facility_id
        assert route["destination_facility_id"] == leg.destination_facility_id

    print("PASS: Route and leg facility relationships are valid")

    # Validate leg sequence and connectivity
    for shipment_id, group in legs.groupby("shipment_id"):
        group = group.sort_values("leg_sequence")

        sequences = group["leg_sequence"].tolist()

        assert sequences == list(range(1, len(group) + 1))

        origins = group["origin_facility_id"].tolist()
        destinations = group["destination_facility_id"].tolist()

        for index in range(len(group) - 1):
            assert destinations[index] == origins[index + 1]

        shipment = shipments.loc[
            shipments["shipment_id"] == shipment_id
        ].iloc[0]

        assert origins[0] == shipment["origin_facility_id"]
        assert destinations[-1] == shipment["destination_facility_id"]

    print("PASS: Leg sequence and route continuity are valid")

    print("\nAll shipment validations passed!")

def validate_tracking_events():
    print("\nValidating tracking events...")

    events = pd.read_csv(DATA_DIR / "tracking_events.csv")
    shipments = pd.read_csv(DATA_DIR / "shipments.csv")
    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    facilities = pd.read_csv(DATA_DIR / "facilities.csv")

    # Primary key
    validate_primary_keys(events, "event_id", "tracking_events")

    # Foreign keys
    assert set(events["shipment_id"]).issubset(
        set(shipments["shipment_id"])
    )

    assert set(events["leg_id"]).issubset(
        set(legs["leg_id"])
    )

    assert set(events["facility_id"]).issubset(
        set(facilities["facility_id"])
    )

    print("PASS: Event foreign keys are valid")

    # Event types
    valid_event_types = {
        "DEPARTED_FACILITY",
        "ARRIVED_FACILITY",
        "DELIVERED"
    }

    assert set(events["event_type"]).issubset(valid_event_types)

    print("PASS: Event types are valid")

    # Event status validation
    valid_statuses = {"VALID", "DUPLICATE"}

    assert set(events["event_status"]).issubset(valid_statuses)

    print("PASS: Event statuses are valid")

    # Timestamp validation
    events["event_time"] = pd.to_datetime(
        events["event_time"], utc=True
    )

    events["ingestion_time"] = pd.to_datetime(
        events["ingestion_time"], utc=True
    )

    assert events["event_time"].notna().all()
    assert events["ingestion_time"].notna().all()

    assert (
        events["ingestion_time"] >= events["event_time"]
    ).all()

    late_events = (
        events["ingestion_time"] > events["event_time"]
    ).sum()

    print("PASS: Timestamp validation completed")
    print(f"Late-arriving events: {late_events}")

    # Facility must match leg origin/destination
    leg_lookup = legs.set_index("leg_id")

    for event in events.itertuples(index=False):
        leg = leg_lookup.loc[event.leg_id]

        if event.event_type == "DEPARTED_FACILITY":
            assert event.facility_id == leg["origin_facility_id"]
        else:
            assert event.facility_id == leg["destination_facility_id"]

    print("PASS: Event and leg facility relationships are valid")

    # Every duplicate must match an original valid event
    comparison_columns = [
        "shipment_id",
        "leg_id",
        "facility_id",
        "event_type",
        "event_time"
    ]

    valid_events = events[
        events["event_status"] == "VALID"
    ]

    duplicate_events = events[
        events["event_status"] == "DUPLICATE"
    ]

    valid_event_keys = set(
        valid_events[comparison_columns].itertuples(
            index=False,
            name=None
        )
    )

    duplicate_event_keys = list(
        duplicate_events[comparison_columns].itertuples(
            index=False,
            name=None
        )
    )

    assert all(
        key in valid_event_keys
        for key in duplicate_event_keys
    ), "A duplicate event has no matching valid original"

    assert (
        duplicate_events["source"] == "CARRIER_API_RETRY"
    ).all()

    print(
        f"PASS: All {len(duplicate_events)} duplicate events "
        "match original valid events"
    )

    # Delivery events must agree with shipment outcomes.
    # Only VALID delivery events count.
    delivered_shipments = set(
        shipments.loc[
            shipments["status"].isin(["DELIVERED", "DELAYED"]),
            "shipment_id"
        ]
    )

    incomplete_shipments = set(
        shipments.loc[
            shipments["status"].isin(["IN_TRANSIT", "CANCELLED"]),
            "shipment_id"
        ]
    )

    actual_delivery_events = set(
        events.loc[
            (events["event_type"] == "DELIVERED")
            & (events["event_status"] == "VALID"),
            "shipment_id"
        ]
    )

    assert actual_delivery_events == delivered_shipments, (
        "Delivery events do not match shipment outcomes"
    )

    assert actual_delivery_events.isdisjoint(
        incomplete_shipments
    )

    print("PASS: Delivery events match shipment outcomes")

    print("\nAll tracking event validations passed!")

def validate_facility_queues():
    print("\nValidating facility queue data...")

    queues = pd.read_csv(DATA_DIR / "facility_queues.csv")
    facilities = pd.read_csv(DATA_DIR / "facilities.csv")

    validate_primary_keys(queues, "queue_id", "facility_queues")

    assert set(queues["facility_id"]).issubset(
        set(facilities["facility_id"])
    )
    print("PASS: Facility foreign keys are valid")

    assert queues["queued_shipments"].ge(0).all()
    assert queues["average_wait_minutes"].ge(0).all()
    assert queues["capacity_utilization_pct"].between(0, 100).all()
    print("PASS: Queue metrics are within valid ranges")

    queues["snapshot_time"] = pd.to_datetime(
        queues["snapshot_time"], utc=True
    )
    assert queues["snapshot_time"].notna().all()
    print("PASS: Queue timestamps are valid")

    print(f"Total queue records: {len(queues)}")
    print("All facility queue validations passed!")
def validate_weather_events():
    print("\nValidating weather disruption data...")

    weather = pd.read_csv(DATA_DIR / "weather_events.csv")
    facilities = pd.read_csv(DATA_DIR / "facilities.csv")
    routes = pd.read_csv(DATA_DIR / "routes.csv")

    validate_primary_keys(
        weather, "weather_event_id", "weather_events"
    )

    valid_facilities = set(facilities["facility_id"])
    valid_routes = set(routes["route_id"])

    assert weather["facility_id"].dropna().isin(valid_facilities).all()
    assert weather["route_id"].dropna().isin(valid_routes).all()
    print("PASS: Weather facility and route references are valid")

    assert (
        weather["facility_id"].notna()
        ^ weather["route_id"].notna()
    ).all()
    print("PASS: Each disruption targets exactly one facility or route")

    valid_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert set(weather["severity"]).issubset(valid_severities)
    print("PASS: Weather severity values are valid")

    weather["start_time"] = pd.to_datetime(
        weather["start_time"], utc=True
    )
    weather["end_time"] = pd.to_datetime(
        weather["end_time"], utc=True
    )

    assert weather["start_time"].notna().all()
    assert weather["end_time"].notna().all()
    assert (weather["end_time"] > weather["start_time"]).all()
    print("PASS: Weather disruption time windows are valid")

    assert weather["delay_impact_minutes"].ge(0).all()
    print("PASS: Delay impact values are valid")

    print(f"Total weather records: {len(weather)}")
    print("All weather validations passed!")
def validate_delivery_outcomes():
    print("\nValidating delivery outcomes...")

    shipments = pd.read_csv(DATA_DIR / "shipments.csv")
    ground_truth = pd.read_csv(DATA_DIR / "ground_truth.csv")
    service_levels = pd.read_csv(DATA_DIR / "service_levels.csv")

    validate_primary_keys(
        ground_truth, "shipment_id", "ground_truth"
    )

    assert set(ground_truth["shipment_id"]) == set(
        shipments["shipment_id"]
    )
    print("PASS: Ground truth covers all shipments")

    valid_statuses = {
        "DELIVERED", "DELAYED", "IN_TRANSIT", "CANCELLED"
    }
    assert set(shipments["status"]).issubset(valid_statuses)
    print("PASS: Shipment statuses are valid")

    delivered_statuses = {"DELIVERED", "DELAYED"}

    completed = shipments["status"].isin(delivered_statuses)
    not_completed = ~completed

    assert shipments.loc[
        completed, "actual_delivery_at"
    ].notna().all()

    assert shipments.loc[
        not_completed, "actual_delivery_at"
    ].isna().all()

    print("PASS: Actual delivery timestamps match shipment status")

    completed_truth = ground_truth[
        ground_truth["delay_label"].isin({"ON_TIME", "LATE"})
    ]

    assert completed_truth["actual_delivery_at"].notna().all()

    expected_delay = (
        pd.to_datetime(
            completed_truth["actual_delivery_at"], utc=True
        )
        - pd.to_datetime(
            completed_truth["promised_delivery_at"], utc=True
        )
    ).dt.total_seconds() / 60

    expected_late = (
        expected_delay > completed_truth["grace_minutes"]
    )

    actual_late = completed_truth["is_late"].astype(int)

    assert (expected_late.astype(int) == actual_late).all()

    print("PASS: Delay labels match SLA grace periods")

    assert set(ground_truth["delay_label"]).issubset({
        "ON_TIME", "LATE", "UNKNOWN", "CANCELLED"
    })

    print("PASS: Ground truth labels are valid")
    print(f"Total ground truth records: {len(ground_truth)}")
    print("All delivery outcome validations passed!")
def validate_route_changes():
    print("\nValidating route changes...")

    changes = pd.read_csv(DATA_DIR / "route_changes.csv")
    segments = pd.read_csv(DATA_DIR / "route_change_segments.csv")
    routes = pd.read_csv(DATA_DIR / "routes.csv")
    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    shipments = pd.read_csv(DATA_DIR / "shipments.csv")

    # Primary keys
    validate_primary_keys(
        changes,
        "route_change_id",
        "route_changes"
    )

    validate_primary_keys(
        segments,
        "segment_id",
        "route_change_segments"
    )

    # Foreign keys
    assert changes["shipment_id"].isin(
        shipments["shipment_id"]
    ).all(), "Invalid shipment references"

    assert changes["leg_id"].isin(
        legs["leg_id"]
    ).all(), "Invalid leg references"

    assert changes["original_route_id"].isin(
        routes["route_id"]
    ).all(), "Invalid original route references"

    assert segments["route_change_id"].isin(
        changes["route_change_id"]
    ).all(), "Invalid route change references"

    assert segments["route_id"].isin(
        routes["route_id"]
    ).all(), "Invalid replacement route references"

    print("PASS: Primary and foreign keys are valid")

    # Exactly two segments per route change.
    segment_counts = segments.groupby(
        "route_change_id"
    ).size()

    assert (segment_counts == 2).all()
    assert set(segment_counts.index) == set(
        changes["route_change_id"]
    )

    print("PASS: Every route change has exactly two segments")

    # Segment sequence must be 1, 2.
    for route_change_id, group in segments.groupby(
        "route_change_id"
    ):
        group = group.sort_values("segment_sequence")

        assert group["segment_sequence"].tolist() == [1, 2]

        assert (
            group.iloc[0]["destination_facility_id"]
            == group.iloc[1]["origin_facility_id"]
        ), f"Disconnected replacement path: {route_change_id}"

    print("PASS: Replacement segments connect correctly")

    # Replacement endpoints must match the original leg.
    check = changes.merge(
        legs[
            [
                "leg_id",
                "origin_facility_id",
                "destination_facility_id",
                "route_id"
            ]
        ],
        on="leg_id",
        suffixes=("_change", "_leg")
    )

    assert (
        check["original_route_id"]
        == check["route_id"]
    ).all(), "Original route reference mismatch"

    first_segments = segments[
        segments["segment_sequence"] == 1
    ].merge(
        changes[["route_change_id", "leg_id"]],
        on="route_change_id"
    ).merge(
        legs[
            [
                "leg_id",
                "origin_facility_id",
                "destination_facility_id"
            ]
        ],
        on="leg_id",
        suffixes=("_segment", "_leg")
    )

    assert (
        first_segments["origin_facility_id_segment"]
        == first_segments["origin_facility_id_leg"]
    ).all()

    last_segments = segments[
        segments["segment_sequence"] == 2
    ].merge(
        changes[["route_change_id", "leg_id"]],
        on="route_change_id"
    ).merge(
        legs[
            [
                "leg_id",
                "origin_facility_id",
                "destination_facility_id"
            ]
        ],
        on="leg_id",
        suffixes=("_segment", "_leg")
    )

    assert (
        last_segments["destination_facility_id_segment"]
        == last_segments["destination_facility_id_leg"]
    ).all()

    print("PASS: Alternative paths preserve original endpoints")

    # Segment route endpoints must match routes.csv.
    route_check = segments.merge(
        routes[
            [
                "route_id",
                "origin_facility_id",
                "destination_facility_id"
            ]
        ],
        on="route_id",
        suffixes=("_segment", "_route")
    )

    assert (
        route_check["origin_facility_id_segment"]
        == route_check["origin_facility_id_route"]
    ).all()

    assert (
        route_check["destination_facility_id_segment"]
        == route_check["destination_facility_id_route"]
    ).all()

    print("PASS: Replacement route endpoints match route master data")

    print("\nAll route-change validations passed!")

if __name__ == "__main__":
    validate_master_data()
    validate_shipments()
    validate_tracking_events()
    validate_facility_queues()
    validate_weather_events()
    validate_delivery_outcomes()
    validate_route_changes()

    print("\n========== ALL DATA VALIDATIONS PASSED ==========")


from functools import lru_cache

import pandas as pd

from src.config import DATA_DIR


@lru_cache(maxsize=1)
def load_eta_data():
    """
    Load and preprocess all ETA datasets once.
    Cached data is reused across shipment predictions.
    """

    shipments = pd.read_csv(DATA_DIR / "shipments.csv")
    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    routes = pd.read_csv(DATA_DIR / "routes.csv")
    events = pd.read_csv(DATA_DIR / "tracking_events.csv")
    queues = pd.read_csv(DATA_DIR / "facility_queues.csv")
    weather = pd.read_csv(DATA_DIR / "weather_events.csv")

    route_changes = pd.read_csv(DATA_DIR / "route_changes.csv")
    route_change_segments = pd.read_csv(
        DATA_DIR / "route_change_segments.csv"
    )

    # Convert timestamps once.
    for column in ["created_at"]:
        shipments[column] = pd.to_datetime(
            shipments[column], utc=True
        )

    legs["leg_sequence"] = pd.to_numeric(
        legs["leg_sequence"]
    )

    for column in ["event_time", "ingestion_time"]:
        events[column] = pd.to_datetime(
            events[column], utc=True
        )

    queues["snapshot_time"] = pd.to_datetime(
        queues["snapshot_time"], utc=True
    )

    for column in ["start_time", "end_time"]:
        weather[column] = pd.to_datetime(
            weather[column], utc=True
        )

    route_changes["change_time"] = pd.to_datetime(
        route_changes["change_time"], utc=True
    )

    # Build lookup dictionaries.
    shipment_lookup = shipments.set_index("shipment_id")

    leg_lookup = {
        shipment_id: group.sort_values("leg_sequence")
        for shipment_id, group in legs.groupby("shipment_id")
    }

    event_lookup = {
        shipment_id: group.sort_values(
            ["event_time", "ingestion_time"]
        )
        for shipment_id, group in events.groupby("shipment_id")
    }

    route_lookup = routes.set_index("route_id")

    queue_lookup = {
        facility_id: group.sort_values("snapshot_time").reset_index(
            drop=True
        )
        for facility_id, group in queues.groupby("facility_id")
    }

    weather_route_lookup = {
        route_id: group
        for route_id, group in weather.dropna(
            subset=["route_id"]
        ).groupby("route_id")
    }

    weather_facility_lookup = {
        facility_id: group
        for facility_id, group in weather.dropna(
            subset=["facility_id"]
        ).groupby("facility_id")
    }

    change_lookup = {
        leg_id: group.sort_values("change_time")
        for leg_id, group in route_changes.groupby("leg_id")
    }

    segment_lookup = {
        change_id: group.sort_values("segment_sequence")
        for change_id, group in route_change_segments.groupby(
            "route_change_id"
        )
    }

    return {
        "shipments": shipment_lookup,
        "legs": leg_lookup,
        "events": event_lookup,
        "routes": route_lookup,
        "queues": queue_lookup,
        "weather_routes": weather_route_lookup,
        "weather_facilities": weather_facility_lookup,
        "route_changes": change_lookup,
        "route_change_segments": segment_lookup
    }


def clear_eta_data_cache():
    """Clear cached datasets after regenerating source data."""
    load_eta_data.cache_clear()


def estimate_shipment_eta(shipment_id, as_of, _data=None):
    """
    Estimate shipment ETA using only information available
    at the specified prediction timestamp.

    Datasets are loaded and preprocessed once, then reused.
    """

    data = _data if _data is not None else load_eta_data()

    if as_of is None or as_of == "":
        as_of = pd.Timestamp.now(tz="UTC")
    else:
        as_of = pd.to_datetime(as_of, utc=True)

    prediction_time = as_of

    # Find shipment.
    shipments = data["shipments"]

    if shipment_id not in shipments.index:
        raise ValueError(f"Shipment not found: {shipment_id}")

    shipment = shipments.loc[shipment_id]

    # Find shipment legs.
    shipment_legs = data["legs"].get(shipment_id)

    if shipment_legs is None or shipment_legs.empty:
        raise ValueError("No shipment legs found")

    # Find events known at prediction time.
    event_matches = data["events"].get(shipment_id)

    latest_event = None

    if event_matches is not None:

        event_matches = event_matches[
            (event_matches["event_time"] <= as_of)
            & (event_matches["ingestion_time"] <= as_of)
            & (event_matches["event_status"] == "VALID")
        ]

        if not event_matches.empty:
            latest_event = event_matches.iloc[-1]

    # Determine current location and remaining legs.
    if latest_event is not None:

        current_location = latest_event["facility_id"]

        latest_leg = shipment_legs[
            shipment_legs["leg_id"] == latest_event["leg_id"]
        ]

        if latest_leg.empty:
            raise ValueError(
                "Tracking event references an unknown leg"
            )

        latest_leg_row = latest_leg.iloc[0]

        current_leg_sequence = int(
            latest_leg_row["leg_sequence"]
        )

        event_type = latest_event["event_type"]

        # Confirmed delivery scan.
        if event_type == "DELIVERED":
            return {
                "shipment_id": shipment_id,
                "prediction_time": as_of.isoformat(),
                "current_location": current_location,
                "base_travel_minutes": 0.0,
                "queue_delay_minutes": 0.0,
                "weather_delay_minutes": 0.0,
                "predicted_eta": latest_event[
                    "event_time"
                ].isoformat(),
                "status": "DELIVERED",
                "delay_reason": None,
                "route_changes_applied": []
            }

        # Detect missing arrival scan.
        if event_type == "DEPARTED_FACILITY":

            planned_arrival = pd.to_datetime(
                latest_leg_row["planned_arrival"],
                utc=True
            )

            if as_of > planned_arrival:

                overdue_minutes = (
                    as_of - planned_arrival
                ).total_seconds() / 60.0

                return {
                    "shipment_id": shipment_id,
                    "prediction_time": as_of.isoformat(),
                    "current_location": current_location,
                    "base_travel_minutes": None,
                    "queue_delay_minutes": 0.0,
                    "weather_delay_minutes": 0.0,
                    "predicted_eta": None,
                    "status": "POTENTIALLY_OVERDUE_NO_SCAN",
                    "delay_reason": "MISSING_ARRIVAL_SCAN",
                    "planned_arrival": planned_arrival.isoformat(),
                    "overdue_minutes": round(
                        overdue_minutes, 2
                    ),
                    "route_changes_applied": []
                }

            remaining_legs = shipment_legs[
                shipment_legs["leg_sequence"]
                >= current_leg_sequence
            ]

        elif event_type == "ARRIVED_FACILITY":

            remaining_legs = shipment_legs[
                shipment_legs["leg_sequence"]
                > current_leg_sequence
            ]

        else:
            raise ValueError(
                f"Unsupported event type: {event_type}"
            )

    else:

        current_location = shipment["origin_facility_id"]
        remaining_legs = shipment_legs

    if remaining_legs.empty:
        return {
            "shipment_id": shipment_id,
            "prediction_time": prediction_time.isoformat(),
            "current_location": current_location,
            "base_travel_minutes": 0.0,
            "queue_delay_minutes": 0.0,
            "weather_delay_minutes": 0.0,
            "predicted_eta": prediction_time.isoformat(),
            "status": "NO_REMAINING_LEGS",
            "delay_reason": None,
            "route_changes_applied": []
        }

    base_minutes = 0.0
    queue_delay_minutes = 0.0
    weather_delay_minutes = 0.0

    route_changes_applied = []

    # Calculate remaining travel and disruption delays.
    for leg in remaining_legs.itertuples(index=False):

        # Find approved route changes known at prediction time.
        effective_changes = data["route_changes"].get(
            leg.leg_id
        )

        selected_change = None

        if effective_changes is not None:

            effective_changes = effective_changes[
                (effective_changes["change_status"] == "APPROVED")
                & (
                    effective_changes["change_time"]
                    <= prediction_time
                )
            ]

            if not effective_changes.empty:
                selected_change = effective_changes.iloc[-1]

        # Build route components.
        if selected_change is not None:

            change_id = selected_change["route_change_id"]

            replacement_segments = data[
                "route_change_segments"
            ].get(change_id)

            if (
                replacement_segments is None
                or replacement_segments.empty
            ):
                raise ValueError(
                    "Route change has no replacement segments: "
                    f"{change_id}"
                )

            route_components = [
                {
                    "route_id": segment.route_id,
                    "destination_facility_id":
                        segment.destination_facility_id
                }
                for segment in replacement_segments.itertuples(
                    index=False
                )
            ]

            route_changes_applied.append(change_id)

        else:

            route_components = [{
                "route_id": leg.route_id,
                "destination_facility_id":
                    leg.destination_facility_id
            }]

        leg_travel_minutes = 0.0

        # Calculate travel and disruption impact.
        for component in route_components:

            route_id = component["route_id"]
            destination = component[
                "destination_facility_id"
            ]

            route = data["routes"].loc[route_id]

            segment_travel_minutes = (
                float(route["distance_km"]) / 55.0
            ) * 60.0

            leg_travel_minutes += segment_travel_minutes

            # Latest queue snapshot available at prediction time.
            facility_queue = data["queues"].get(destination)

            if facility_queue is not None:

                queue_position = facility_queue[
                    "snapshot_time"
                ].searchsorted(
                    prediction_time,
                    side="right"
                ) - 1

                if queue_position >= 0:

                    latest_queue = facility_queue.iloc[
                        queue_position
                    ]

                    queue_delay_minutes += float(
                        latest_queue["average_wait_minutes"]
                    )

            # Weather affecting the route or destination.
            route_weather = data[
                "weather_routes"
            ].get(route_id)

            facility_weather = data[
                "weather_facilities"
            ].get(destination)

            weather_frames = []

            if route_weather is not None:
                weather_frames.append(route_weather)

            if facility_weather is not None:
                weather_frames.append(facility_weather)

            if weather_frames:

                relevant_weather = pd.concat(
                    weather_frames
                ).drop_duplicates(
                    subset=["weather_event_id"]
                )

                active_weather = relevant_weather[
                    (
                        relevant_weather["start_time"]
                        <= prediction_time
                    )
                    & (
                        relevant_weather["end_time"]
                        >= prediction_time
                    )
                ]

                weather_delay_minutes += float(
                    active_weather[
                        "delay_impact_minutes"
                    ].sum()
                )

        # Subtract elapsed time on the active leg.
        if (
            latest_event is not None
            and latest_event["event_type"] == "DEPARTED_FACILITY"
            and latest_event["leg_id"] == leg.leg_id
        ):

            elapsed_minutes = max(
                (
                    as_of - latest_event["event_time"]
                ).total_seconds() / 60.0,
                0.0
            )

            leg_travel_minutes = max(
                leg_travel_minutes - elapsed_minutes,
                0.0
            )

        base_minutes += leg_travel_minutes

    # Calculate final ETA.
    total_minutes = (
        base_minutes
        + queue_delay_minutes
        + weather_delay_minutes
    )

    predicted_eta = (
        prediction_time
        + pd.Timedelta(minutes=total_minutes)
    )

    return {
        "shipment_id": shipment_id,
        "prediction_time": prediction_time.isoformat(),
        "current_location": current_location,
        "base_travel_minutes": round(base_minutes, 2),
        "queue_delay_minutes": round(queue_delay_minutes, 2),
        "weather_delay_minutes": round(weather_delay_minutes, 2),
        "predicted_eta": predicted_eta.isoformat(),
        "status": "IN_TRANSIT",
        "delay_reason": None,
        "route_changes_applied": route_changes_applied
    }

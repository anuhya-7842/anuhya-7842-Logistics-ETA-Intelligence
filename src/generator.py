import argparse
import json
import random
import pandas as pd
from datetime import datetime, timezone, timedelta

from src.config import (
    RANDOM_SEED,
    DATA_DIR,
    STARTER_CONFIG,
    FULL_CONFIG,
)


def generate_carriers(rng):
    carriers = []

    carrier_types = ["ROAD", "AIR", "RAIL", "SEA"]

    for i in range(1, 21):
        carrier_type = carrier_types[(i - 1) % len(carrier_types)]

        carriers.append({
            "carrier_id": f"CAR-{i:03d}",
            "carrier_name": f"Logistics Carrier {i:03d}",
            "carrier_type": carrier_type,
            "operating_status": "ACTIVE",
            "service_rating": round(rng.uniform(3.0, 5.0), 2),
            "operating_days": "MON,TUE,WED,THU,FRI,SAT,SUN",
            "operating_start_hour": 0,
            "operating_end_hour": 24
        })

    return pd.DataFrame(carriers)


def generate_facilities(rng, facility_count=100):
    facilities = []

    facility_types = ["WAREHOUSE", "HUB", "PORT"]

    cities = [
        "Hyderabad", "Mumbai", "Delhi", "Chennai", "Bangalore",
        "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Kochi",
        "Nagpur", "Lucknow", "Indore", "Bhopal", "Surat",
        "Visakhapatnam", "Coimbatore", "Guwahati", "Patna", "Noida"
    ]

    for i in range(1, facility_count + 1):
        facilities.append({
            "facility_id": f"FAC-{i:04d}",
            "facility_name": f"Logistics Facility {i:03d}",
            "city": cities[(i - 1) % len(cities)],
            "country": "India",
            "facility_type": rng.choice(facility_types),
            "timezone": "Asia/Kolkata",
            "operating_hours": "00:00-23:59",
            "operating_days": "MON,TUE,WED,THU,FRI,SAT,SUN",
            "operating_start_hour": 0,
            "operating_end_hour": 24
        })

    return pd.DataFrame(facilities)


def generate_routes(facilities, rng, route_count=300):
    routes = []

    facility_ids = facilities["facility_id"].tolist()
    route_pairs = set()

    while len(routes) < route_count:
        origin = rng.choice(facility_ids)
        destination = rng.choice(facility_ids)

        if origin == destination:
            continue

        pair = (origin, destination)

        if pair in route_pairs:
            continue

        route_pairs.add(pair)

        routes.append({
            "route_id": f"RTE-2026-{len(routes) + 1:06d}",
            "origin_facility_id": origin,
            "destination_facility_id": destination,
            "distance_km": round(rng.uniform(50, 3000), 2),
            "transport_mode": rng.choice(["ROAD", "AIR", "RAIL", "SEA"]),
            "route_status": "ACTIVE"
        })

    return pd.DataFrame(routes)


def generate_service_levels():
    service_levels = [
        {
            "service_level_id": "SVC-001",
            "service_name": "STANDARD",
            "target_delivery_hours": 120,
            "delay_grace_hours": 12,
            "effective_from": "2026-01-01T00:00:00Z",
            "effective_to": None
        },
        {
            "service_level_id": "SVC-002",
            "service_name": "EXPRESS",
            "target_delivery_hours": 72,
            "delay_grace_hours": 6,
            "effective_from": "2026-01-01T00:00:00Z",
            "effective_to": None
        },
        {
            "service_level_id": "SVC-003",
            "service_name": "PREMIUM",
            "target_delivery_hours": 24,
            "delay_grace_hours": 2,
            "effective_from": "2026-01-01T00:00:00Z",
            "effective_to": None
        }
    ]

    return pd.DataFrame(service_levels)


def generate_master_data(config=None):
    if config is None:
        config = STARTER_CONFIG

    rng = random.Random(RANDOM_SEED)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating master data...")

    carriers = generate_carriers(rng)
    facilities = generate_facilities(
        rng,
        facility_count=config["facilities"]
    )
    routes = generate_routes(
        facilities,
        rng,
        route_count=max(300, config["facilities"] * 3)
    )
    service_levels = generate_service_levels()

    datasets = {
        "carriers": carriers,
        "facilities": facilities,
        "routes": routes,
        "service_levels": service_levels
    }

    for name, dataframe in datasets.items():
        filepath = DATA_DIR / f"{name}.csv"
        dataframe.to_csv(filepath, index=False)
        print(f"{name}: {len(dataframe)} records saved")

    print("\nMaster data generation completed!")

    return datasets


def generate_shipments_and_legs(master_data, shipment_count=None):
    if shipment_count is None:
        shipment_count = STARTER_CONFIG["shipments"]

    rng = random.Random(RANDOM_SEED)

    shipments = []
    shipment_legs = []
    new_routes = []

    carriers = master_data["carriers"]
    facilities = master_data["facilities"]
    routes = master_data["routes"]
    services = master_data["service_levels"]

    facility_ids = facilities["facility_id"].tolist()
    carrier_ids = carriers["carrier_id"].tolist()
    service_records = services.to_dict("records")

    # Index routes by origin and destination.
    route_lookup = {}

    for route in routes.to_dict("records"):
        key = (
            route["origin_facility_id"],
            route["destination_facility_id"]
        )
        route_lookup.setdefault(key, []).append(route)

    base_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for i in range(1, shipment_count + 1):
        shipment_id = f"SHP-2026-{i:06d}"

        origin = rng.choice(facility_ids)
        destination = rng.choice(
            [f for f in facility_ids if f != origin]
        )

        carrier_id = rng.choice(carrier_ids)
        service = rng.choice(service_records)

        created_at = base_date + timedelta(
            days=rng.randint(0, 300),
            hours=rng.randint(0, 23)
        )

        promised_delivery = created_at + timedelta(
            hours=service["target_delivery_hours"]
        )

        leg_count = rng.randint(2, 4)

        intermediate = [
            f for f in facility_ids
            if f not in (origin, destination)
        ]

        selected_intermediate = rng.sample(
            intermediate, leg_count - 1
        )

        route_facilities = [
            origin, *selected_intermediate, destination
        ]

        current_departure = created_at

        for leg_number in range(1, leg_count + 1):
            leg_origin = route_facilities[leg_number - 1]
            leg_destination = route_facilities[leg_number]

            route_key = (leg_origin, leg_destination)

            matching_routes = route_lookup.get(route_key, [])

            if not matching_routes:
                selected_route = {
                    "route_id": (
                        f"RTE-GEN-{shipment_id}-{leg_number:02d}"
                    ),
                    "origin_facility_id": leg_origin,
                    "destination_facility_id": leg_destination,
                    "distance_km": round(
                        rng.uniform(50, 3000), 2
                    ),
                    "transport_mode": "ROAD",
                    "route_status": "ACTIVE"
                }

                new_routes.append(selected_route)

                # Keep the lookup updated for later shipments.
                route_lookup.setdefault(route_key, []).append(
                    selected_route
                )
            else:
                selected_route = rng.choice(matching_routes)

            leg_id = f"LEG-{shipment_id}-{leg_number:02d}"

            travel_hours = max(
                2,
                int(selected_route["distance_km"] / 55)
            )

            planned_arrival = current_departure + timedelta(
                hours=travel_hours
            )

            shipment_legs.append({
                "leg_id": leg_id,
                "shipment_id": shipment_id,
                "route_id": selected_route["route_id"],
                "carrier_id": carrier_id,
                "origin_facility_id": leg_origin,
                "destination_facility_id": leg_destination,
                "leg_sequence": leg_number,
                "planned_departure": current_departure.isoformat(),
                "planned_arrival": planned_arrival.isoformat(),
                "actual_departure": None,
                "actual_arrival": None
            })

            current_departure = planned_arrival + timedelta(hours=2)

        shipments.append({
            "shipment_id": shipment_id,
            "customer_id": f"CUST-{rng.randint(1, 10000):06d}",
            "origin_facility_id": origin,
            "destination_facility_id": destination,
            "carrier_id": carrier_id,
            "service_level_id": service["service_level_id"],
            "created_at": created_at.isoformat(),
            "promised_delivery_at": promised_delivery.isoformat(),
            "actual_delivery_at": None,
            "status": "CREATED",
            "current_eta": current_departure.isoformat()
        })

    # Append generated routes only once.
    if new_routes:
        routes = pd.concat(
            [routes, pd.DataFrame(new_routes)],
            ignore_index=True
        )

    routes.to_csv(DATA_DIR / "routes.csv", index=False)

    shipment_df = pd.DataFrame(shipments)
    legs_df = pd.DataFrame(shipment_legs)

    shipment_df.to_csv(
        DATA_DIR / "shipments.csv", index=False
    )

    legs_df.to_csv(
        DATA_DIR / "shipment_legs.csv", index=False
    )

    print(f"Generated {len(shipment_df)} shipments")
    print(f"Generated {len(legs_df)} shipment legs")
    print(f"Generated {len(new_routes)} additional routes")

    return shipment_df, legs_df


def generate_tracking_events(shipment_count=None):
    print("Generating tracking events...")

    rng = random.Random(RANDOM_SEED + 1)
    duplicate_rng = random.Random(RANDOM_SEED + 11)

    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    shipments = pd.read_csv(DATA_DIR / "shipments.csv")

    # Convert shipment timestamps only once.
    shipments["actual_delivery_at"] = pd.to_datetime(
        shipments["actual_delivery_at"],
        utc=True,
        errors="coerce"
    )

    shipment_status = shipments.set_index(
        "shipment_id"
    )["status"].to_dict()

    actual_delivery = shipments.set_index(
        "shipment_id"
    )["actual_delivery_at"].to_dict()

    if shipment_count is not None:
        allowed_shipments = set(
            shipments["shipment_id"].head(shipment_count)
        )
        legs = legs[
            legs["shipment_id"].isin(allowed_shipments)
        ]

    # Convert leg timestamps once instead of inside the loop.
    legs["planned_departure"] = pd.to_datetime(
        legs["planned_departure"],
        utc=True
    )

    legs["planned_arrival"] = pd.to_datetime(
        legs["planned_arrival"],
        utc=True
    )

    events = []
    event_counters = {}

    for shipment_id, shipment_legs in legs.groupby(
        "shipment_id",
        sort=False
    ):
        status = shipment_status[shipment_id]

        shipment_legs = shipment_legs.sort_values(
            "leg_sequence"
        )

        final_leg_sequence = shipment_legs[
            "leg_sequence"
        ].max()

        if status in ["CANCELLED", "IN_TRANSIT"]:
            completed_legs = shipment_legs.iloc[:-1]
        else:
            completed_legs = shipment_legs

        event_counters[shipment_id] = 0

        for leg in completed_legs.itertuples(index=False):

            planned_departure = leg.planned_departure
            planned_arrival = leg.planned_arrival

            # Departure event.
            departure_time = planned_departure + timedelta(
                minutes=rng.randint(-30, 180)
            )

            event_counters[shipment_id] += 1

            events.append({
                "event_id": (
                    f"EVT-{shipment_id}-"
                    f"{event_counters[shipment_id]:06d}"
                ),
                "shipment_id": shipment_id,
                "leg_id": leg.leg_id,
                "facility_id": leg.origin_facility_id,
                "event_type": "DEPARTED_FACILITY",
                "event_time": departure_time.isoformat(),
                "ingestion_time": (
                    departure_time + timedelta(
                        minutes=rng.randint(1, 120)
                    )
                ).isoformat(),
                "event_status": "VALID",
                "source": "CARRIER_API"
            })

            # Arrival or delivery event.
            is_final_leg = (
                leg.leg_sequence == final_leg_sequence
            )

            if is_final_leg:
                arrival_time = actual_delivery[shipment_id]

                if pd.isna(arrival_time):
                    continue

                event_type = "DELIVERED"
            else:
                arrival_time = planned_arrival + timedelta(
                    minutes=rng.randint(-30, 360)
                )
                event_type = "ARRIVED_FACILITY"

            event_counters[shipment_id] += 1

            events.append({
                "event_id": (
                    f"EVT-{shipment_id}-"
                    f"{event_counters[shipment_id]:06d}"
                ),
                "shipment_id": shipment_id,
                "leg_id": leg.leg_id,
                "facility_id": leg.destination_facility_id,
                "event_type": event_type,
                "event_time": arrival_time.isoformat(),
                "ingestion_time": (
                    arrival_time + timedelta(
                        minutes=rng.randint(1, 180)
                    )
                ).isoformat(),
                "event_status": "VALID",
                "source": "CARRIER_API"
            })

    # Generate duplicate carrier scans.
    original_events = list(events)
    duplicate_count = 0

    for original in original_events:

        if duplicate_rng.random() < 0.02:

            duplicate = original.copy()

            shipment_id = duplicate["shipment_id"]

            event_counters[shipment_id] += 1

            duplicate["event_id"] = (
                f"EVT-{shipment_id}-"
                f"{event_counters[shipment_id]:06d}"
            )

            original_ingestion = pd.Timestamp(
                duplicate["ingestion_time"]
            )

            duplicate["ingestion_time"] = (
                original_ingestion + timedelta(
                    minutes=duplicate_rng.randint(5, 60)
                )
            ).isoformat()

            duplicate["event_status"] = "DUPLICATE"
            duplicate["source"] = "CARRIER_API_RETRY"

            events.append(duplicate)
            duplicate_count += 1

    events_df = pd.DataFrame(events)

    events_df.to_csv(
        DATA_DIR / "tracking_events.csv",
        index=False
    )

    print(f"Generated {len(events_df)} tracking events")
    print(f"Duplicate events generated: {duplicate_count}")

    print("\nEvent type distribution:")
    print(events_df["event_type"].value_counts())

    print("\nEvent status distribution:")
    print(events_df["event_status"].value_counts())

    print("\nEvents by shipment outcome:")
    print(
        events_df.merge(
            shipments[["shipment_id", "status"]],
            on="shipment_id"
        ).groupby(
            ["status", "event_type"]
        ).size()
    )

    return events_df

def generate_route_changes():
    print("Generating route changes...")

    rng = random.Random(RANDOM_SEED + 12)

    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    routes = pd.read_csv(DATA_DIR / "routes.csv")
    shipments = pd.read_csv(DATA_DIR / "shipments.csv")

    active_routes = routes[
        routes["route_status"] == "ACTIVE"
    ].copy()

    shipment_status = shipments.set_index(
        "shipment_id"
    )["status"].to_dict()

    shipment_created_lookup = shipments.set_index(
        "shipment_id"
    )["created_at"].to_dict()

    route_lookup = {}

    for route in active_routes.itertuples():
        key = (
            route.origin_facility_id,
            route.destination_facility_id
        )
        route_lookup.setdefault(key, []).append(route)

    eligible_shipments = sorted(
        shipment_id
        for shipment_id, status in shipment_status.items()
        if status != "CANCELLED"
    )

    change_count = max(
        1,
        int(len(eligible_shipments) * 0.05)
    )

    selected_shipments = rng.sample(
        eligible_shipments,
        min(change_count, len(eligible_shipments))
    )

    route_changes = []
    route_change_segments = []

    for shipment_id in selected_shipments:

        shipment_legs = legs[
            legs["shipment_id"] == shipment_id
        ].sort_values("leg_sequence")

        if shipment_legs.empty:
            continue

        selected_leg = shipment_legs.iloc[
            rng.randrange(len(shipment_legs))
        ]

        origin = selected_leg["origin_facility_id"]
        destination = selected_leg["destination_facility_id"]

        original_route_id = selected_leg["route_id"]

        intermediate_facilities = sorted({
            middle
            for (start, middle) in route_lookup
            if start == origin
            and middle not in (origin, destination)
            and (middle, destination) in route_lookup
        })

        if not intermediate_facilities:
            continue

        middle = rng.choice(intermediate_facilities)

        first_options = route_lookup[(origin, middle)]
        second_options = route_lookup[(middle, destination)]

        first_route = rng.choice(first_options)
        second_route = rng.choice(second_options)

        shipment_created_at = pd.to_datetime(
            shipment_created_lookup[shipment_id],
            utc=True
        )

        planned_departure = pd.to_datetime(
            selected_leg["planned_departure"],
            utc=True
        )

        earliest_change_time = (
            shipment_created_at + timedelta(minutes=1)
        )

        available_seconds = int(
            (planned_departure - earliest_change_time).total_seconds()
        )

        if available_seconds < 1:
            continue

        change_time = earliest_change_time + timedelta(
            seconds=rng.randint(0, available_seconds)
        )

        route_change_id = (
            f"RCH-2026-{len(route_changes) + 1:06d}"
        )

        route_changes.append({
            "route_change_id": route_change_id,
            "shipment_id": shipment_id,
            "leg_id": selected_leg["leg_id"],
            "original_route_id": original_route_id,
            "change_time": change_time.isoformat(),
            "reason": rng.choice([
                "WEATHER_DISRUPTION",
                "FACILITY_CONGESTION",
                "ROAD_CLOSURE",
                "OPERATIONAL_OPTIMIZATION"
            ]),
            "change_status": "APPROVED",
            "source": "ROUTE_OPTIMIZATION_ENGINE"
        })

        route_change_segments.append({
            "segment_id": f"{route_change_id}-01",
            "route_change_id": route_change_id,
            "segment_sequence": 1,
            "route_id": first_route.route_id,
            "origin_facility_id": origin,
            "destination_facility_id": middle,
            "distance_km": first_route.distance_km,
            "transport_mode": first_route.transport_mode
        })

        route_change_segments.append({
            "segment_id": f"{route_change_id}-02",
            "route_change_id": route_change_id,
            "segment_sequence": 2,
            "route_id": second_route.route_id,
            "origin_facility_id": middle,
            "destination_facility_id": destination,
            "distance_km": second_route.distance_km,
            "transport_mode": second_route.transport_mode
        })

    changes_df = pd.DataFrame(route_changes)
    segments_df = pd.DataFrame(route_change_segments)

    changes_df.to_csv(
        DATA_DIR / "route_changes.csv",
        index=False
    )

    segments_df.to_csv(
        DATA_DIR / "route_change_segments.csv",
        index=False
    )

    print(f"Generated {len(changes_df)} route changes")
    print(f"Generated {len(segments_df)} replacement segments")

    if not changes_df.empty:
        print("\nRoute change reasons:")
        print(changes_df["reason"].value_counts())

    return changes_df, segments_df

def generate_facility_queues():
    print("Generating facility queue data...")

    rng = random.Random(RANDOM_SEED + 2)

    facilities = pd.read_csv(DATA_DIR / "facilities.csv")

    queue_records = []
    queue_counter = 1

    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for facility in facilities.itertuples(index=False):
        for day in range(300):
            for hour in [0, 6, 12, 18]:
                snapshot_time = start_time + timedelta(
                    days=day,
                    hours=hour
                )

                queue_records.append({
                    "queue_id": f"QUE-{queue_counter:06d}",
                    "facility_id": facility.facility_id,
                    "snapshot_time": snapshot_time.isoformat(),
                    "queued_shipments": rng.randint(0, 50),
                    "average_wait_minutes": round(
                        rng.uniform(0, 360), 2
                    ),
                    "capacity_utilization_pct": round(
                        rng.uniform(10, 100), 2
                    ),
                    "queue_status": "HIGH"
                    if rng.random() < 0.2 else "NORMAL"
                })

                queue_counter += 1

    queue_df = pd.DataFrame(queue_records)

    queue_df.to_csv(
        DATA_DIR / "facility_queues.csv",
        index=False
    )

    print(f"Generated {len(queue_df)} facility queue records")

def generate_weather_events(disruption_count=None):
    if disruption_count is None:
        disruption_count = STARTER_CONFIG["disruption_windows"]
    print("Generating weather disruption data...")

    rng = random.Random(RANDOM_SEED + 3)

    facilities = pd.read_csv(DATA_DIR / "facilities.csv")
    routes = pd.read_csv(DATA_DIR / "routes.csv")

    weather_types = [
        "HEAVY_RAIN",
        "FLOOD",
        "STORM",
        "FOG",
        "EXTREME_HEAT",
        "STRONG_WINDS",
    ]

    records = []

    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for i in range(disruption_count):
        start_offset = rng.randint(0, 290 * 24)
        event_start = start_time + timedelta(hours=start_offset)
        duration = rng.randint(2, 48)

        event_type = rng.choice(weather_types)
        severity = rng.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        applies_to_route = rng.random() < 0.5

        if applies_to_route:
            route = routes.iloc[rng.randrange(len(routes))]
            facility_id = None
            route_id = route["route_id"]
        else:
            facility = facilities.iloc[rng.randrange(len(facilities))]
            facility_id = facility["facility_id"]
            route_id = None

        records.append({
            "weather_event_id": f"WTH-2026-{i + 1:06d}",
            "facility_id": facility_id,
            "route_id": route_id,
            "weather_type": event_type,
            "severity": severity,
            "start_time": event_start.isoformat(),
            "end_time": (event_start + timedelta(hours=duration)).isoformat(),
            "delay_impact_minutes": rng.randint(15, 720),
            "source": "SYNTHETIC_WEATHER_FEED",
        })

    weather_df = pd.DataFrame(records)

    weather_df.to_csv(
        DATA_DIR / "weather_events.csv",
        index=False
    )

    print(f"Generated {len(weather_df)} weather disruption records")
def generate_delivery_outcomes():
    print("Generating actual delivery outcomes...")

    rng = random.Random(RANDOM_SEED + 4)

    shipments = pd.read_csv(DATA_DIR / "shipments.csv")
    shipments["actual_delivery_at"] = shipments[
        "actual_delivery_at"
    ].astype("object")
    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    service_levels = pd.read_csv(DATA_DIR / "service_levels.csv")

    shipments["promised_delivery_at"] = pd.to_datetime(
        shipments["promised_delivery_at"], utc=True
    )

    legs["planned_arrival"] = pd.to_datetime(
        legs["planned_arrival"], utc=True
    )

    service_lookup = service_levels.set_index("service_level_id")

    final_arrival_lookup = (
        legs.sort_values("leg_sequence")
        .groupby("shipment_id")["planned_arrival"]
        .last()
        .to_dict()
    )

    ground_truth_records = []

    for index, shipment in shipments.iterrows():

        shipment_id = shipment["shipment_id"]

        service = service_lookup.loc[shipment["service_level_id"]]

        grace_minutes = int(
            service["delay_grace_hours"] * 60
        )

        promised_time = shipment["promised_delivery_at"]

        final_planned_arrival = final_arrival_lookup[shipment_id]

        outcome = rng.random()

        if outcome < 0.02:
            status = "CANCELLED"
            actual_delivery = None
            delay_minutes = None
            is_late = None
            delay_label = "CANCELLED"

        elif outcome < 0.10:
            status = "IN_TRANSIT"
            actual_delivery = None
            delay_minutes = None
            is_late = None
            delay_label = "UNKNOWN"

        else:
            # Generate early, on-time, and late deliveries.
            deviation_minutes = rng.randint(-240, 900)

            actual_delivery = (
                promised_time
                + pd.Timedelta(minutes=deviation_minutes)
            )

            delay_minutes = max(
                0,
                int(
                    (
                        actual_delivery - promised_time
                    ).total_seconds() / 60
                )
            )

            is_late = int(deviation_minutes > grace_minutes)

            if is_late:
                status = "DELAYED"
                delay_label = "LATE"
            else:
                status = "DELIVERED"
                delay_label = "ON_TIME"

        shipments.at[index, "status"] = status

        shipments.at[index, "actual_delivery_at"] = (
            actual_delivery.isoformat()
            if actual_delivery is not None
            else None
        )

        if actual_delivery is not None:
            shipments.at[index, "current_eta"] = (
                actual_delivery.isoformat()
            )
        else:
            shipments.at[index, "current_eta"] = (
                final_planned_arrival.isoformat()
            )

        ground_truth_records.append({
            "shipment_id": shipment_id,
            "promised_delivery_at": promised_time.isoformat(),
            "actual_delivery_at": (
                actual_delivery.isoformat()
                if actual_delivery is not None
                else None
            ),
            "delay_minutes": delay_minutes,
            "grace_minutes": grace_minutes,
            "is_late": is_late,
            "delay_label": delay_label,
            "final_status": status,
        })

    shipments.to_csv(
        DATA_DIR / "shipments.csv",
        index=False
    )

    ground_truth = pd.DataFrame(ground_truth_records)

    ground_truth.to_csv(
        DATA_DIR / "ground_truth.csv",
        index=False
    )

    print(f"Processed {len(shipments)} shipments")
    print("\nShipment status distribution:")
    print(shipments["status"].value_counts())

    print("\nDelivery labels:")
    print(ground_truth["delay_label"].value_counts())

    print("\nGenerated ground_truth.csv")

def generate_anomaly_ground_truth():
    print("\nGenerating isolated anomaly scenarios...")

    shipments = pd.read_csv(DATA_DIR / "shipments.csv")
    legs = pd.read_csv(DATA_DIR / "shipment_legs.csv")
    events = pd.read_csv(DATA_DIR / "tracking_events.csv")

    scenarios = []
    anomaly_records = []

    # ANOM-001: Ingestion time earlier than event time
    valid_event = events[
        events["event_status"] == "VALID"
    ].iloc[0]

    invalid_event = valid_event.to_dict()
    invalid_event["event_id"] = "ANOM-EVT-001"

    invalid_event["event_time"] = (
        pd.to_datetime(valid_event["ingestion_time"], utc=True)
        + pd.Timedelta(hours=2)
    ).isoformat()

    anomaly_records.append({
        "scenario_id": "ANOM-001",
        "issue_type": "INGESTION_TIME_BEFORE_EVENT_TIME",
        "record_type": "TRACKING_EVENT",
        "record": invalid_event,
    })

    scenarios.append({
        "scenario_id": "ANOM-001",
        "issue_type": "INGESTION_TIME_BEFORE_EVENT_TIME",
        "affected_entity_type": "TRACKING_EVENT",
        "affected_entity_id": "ANOM-EVT-001",
        "observed_condition": "ingestion_time is earlier than event_time",
        "expected_behavior": "REJECT_OR_QUARANTINE_INVALID_EVENT",
        "ground_truth_label": "INVALID_TIMESTAMP_ORDER",
    })

    # ANOM-002: Impossible route sequence
    shipment_groups = legs.groupby("shipment_id")

    selected_shipment_id = next(
        shipment_id
        for shipment_id, group in shipment_groups
        if len(group) >= 2
    )

    selected_legs = (
        legs[legs["shipment_id"] == selected_shipment_id]
        .sort_values("leg_sequence")
        .head(2)
    )

    first_leg = {
        key: (None if pd.isna(value) else value)
        for key, value in selected_legs.iloc[0].to_dict().items()
    }

    second_leg = {
        key: (None if pd.isna(value) else value)
        for key, value in selected_legs.iloc[1].to_dict().items()
    }

    first_sequence = int(first_leg["leg_sequence"])
    second_sequence = int(second_leg["leg_sequence"])

    first_leg["leg_sequence"] = second_sequence
    second_leg["leg_sequence"] = first_sequence

    anomaly_records.append({
        "scenario_id": "ANOM-002",
        "issue_type": "IMPOSSIBLE_ROUTE_ORDER",
        "record_type": "SHIPMENT_LEGS",
        "records": [first_leg, second_leg],
    })

    scenarios.append({
        "scenario_id": "ANOM-002",
        "issue_type": "IMPOSSIBLE_ROUTE_ORDER",
        "affected_entity_type": "SHIPMENT",
        "affected_entity_id": selected_shipment_id,
        "observed_condition": "Two consecutive leg sequence numbers are reversed",
        "expected_behavior": "REJECT_INVALID_LEG_SEQUENCE",
        "ground_truth_label": "INVALID_ROUTE_SEQUENCE",
    })

    # ANOM-003: Future event leakage
    future_event = events[
        events["event_status"] == "VALID"
    ].iloc[0].to_dict()

    prediction_time = (
        pd.to_datetime(future_event["event_time"], utc=True)
        - pd.Timedelta(hours=1)
    )

    anomaly_records.append({
        "scenario_id": "ANOM-003",
        "issue_type": "FUTURE_EVENT_LEAKAGE",
        "record_type": "ETA_PREDICTION_CASE",
        "prediction_as_of": prediction_time.isoformat(),
        "future_event": future_event,
    })

    scenarios.append({
        "scenario_id": "ANOM-003",
        "issue_type": "FUTURE_EVENT_LEAKAGE",
        "affected_entity_type": "TRACKING_EVENT",
        "affected_entity_id": future_event["event_id"],
        "observed_condition": "Event timestamp is later than prediction time",
        "expected_behavior": "EXCLUDE_EVENT_FROM_HISTORICAL_ETA",
        "ground_truth_label": "FUTURE_EVENT_MUST_NOT_BE_USED",
    })

    # ANOM-004: Delivered shipment marked as in transit
    delivered_events = events[
        (events["event_type"] == "DELIVERED")
        & (events["event_status"] == "VALID")
    ]

    delivered_shipments = shipments[
        shipments["status"].isin(["DELIVERED", "DELAYED"])
    ]

    delivered_match = delivered_events.merge(
        delivered_shipments[["shipment_id", "status"]],
        on="shipment_id",
        how="inner"
    ).iloc[0]

    anomaly_records.append({
        "scenario_id": "ANOM-004",
        "issue_type": "DELIVERED_SHIPMENT_MARKED_IN_TRANSIT",
        "record_type": "SHIPMENT_STATUS_CONFLICT",
        "shipment_id": delivered_match["shipment_id"],
        "baseline_status": delivered_match["status"],
        "anomalous_status": "IN_TRANSIT",
        "delivered_event_present": True,
    })

    scenarios.append({
        "scenario_id": "ANOM-004",
        "issue_type": "DELIVERED_SHIPMENT_MARKED_IN_TRANSIT",
        "affected_entity_type": "SHIPMENT",
        "affected_entity_id": delivered_match["shipment_id"],
        "observed_condition": "Delivered event exists but shipment status is IN_TRANSIT",
        "expected_behavior": "FLAG_SHIPMENT_STATUS_CONFLICT",
        "ground_truth_label": "DELIVERED_STATUS_CONFLICT",
    })

    # Save anomaly ground truth
    anomaly_ground_truth = pd.DataFrame(scenarios)

    anomaly_ground_truth.to_csv(
        DATA_DIR / "anomaly_ground_truth.csv",
        index=False
    )

    # Save isolated anomalous records
    with open(DATA_DIR / "anomaly_records.json", "w", encoding="utf-8") as file:
        json.dump(anomaly_records, file, indent=4, default=str)

    print(f"Generated {len(anomaly_ground_truth)} anomaly scenarios")
    print("Generated anomaly_ground_truth.csv")
    print("Generated anomaly_records.json")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate Logistics ETA datasets"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Generate the full-scale dataset"
    )

    args = parser.parse_args()

    config = FULL_CONFIG if args.full else STARTER_CONFIG

    print("\n========== LOGISTICS ETA DATA GENERATION ==========\n")
    print(f"Dataset mode: {'FULL' if args.full else 'STARTER'}")
    print(f"Shipment target: {config['shipments']:,}")
    print(f"Facility target: {config['facilities']:,}")
    print(f"Weather disruption target: {config['disruption_windows']:,}")

    # 1. Generate master data
    master_data = generate_master_data(config)

    # 2. Generate shipments and shipment legs
    generate_shipments_and_legs(
        master_data,
        shipment_count=config["shipments"]
    )

    # 3. Generate delivery outcomes and ground truth
    generate_delivery_outcomes()

    # 4. Generate tracking events
    generate_tracking_events()

    # 5. Generate route changes
    generate_route_changes()

    # 6. Generate facility queue snapshots
    generate_facility_queues()

    # 7. Generate weather disruptions
    generate_weather_events(
        disruption_count=config["disruption_windows"]
    )

    # 8. Generate isolated anomaly ground truth
    generate_anomaly_ground_truth()

    print("\n========== DATA GENERATION COMPLETED ==========\n")

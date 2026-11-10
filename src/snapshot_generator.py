
import pandas as pd

from src.config import DATA_DIR, ETA_SNAPSHOT_INTERVAL_HOURS
from src.eta_engine import estimate_shipment_eta, load_eta_data


def generate_eta_snapshots():

    shipments = pd.read_csv(DATA_DIR / "shipments.csv").head(1000)

    shipments["created_at"] = pd.to_datetime(
        shipments["created_at"],
        utc=True
    )

    shipments["actual_delivery_at"] = pd.to_datetime(
        shipments["actual_delivery_at"],
        utc=True,
        errors="coerce"
    )

    eta_data = load_eta_data()

    latest_queue_time = max(
        group["snapshot_time"].max()
        for group in eta_data["queues"].values()
    )

    cutoff_time = latest_queue_time

    interval = pd.Timedelta(
        hours=ETA_SNAPSHOT_INTERVAL_HOURS
    )

    snapshots = []
    skipped_shipments = 0

    print("Generating historical ETA snapshots...")
    print(f"Historical cutoff: {cutoff_time}")

    for index, (_, shipment) in enumerate(shipments.iterrows()):

        shipment_id = shipment["shipment_id"]
        status = shipment["status"]

        if status == "CANCELLED":
            skipped_shipments += 1
            continue

        start_time = shipment["created_at"]

        if status in {"DELIVERED", "DELAYED"}:
            actual_delivery = shipment["actual_delivery_at"]

            if pd.isna(actual_delivery):
                skipped_shipments += 1
                continue

            end_time = min(actual_delivery, cutoff_time)

        else:
            end_time = cutoff_time

        if start_time > end_time:
            skipped_shipments += 1
            continue

        # Generate the regular six-hour prediction schedule.
        prediction_times = []
        prediction_time = start_time

        while prediction_time <= end_time:
            prediction_times.append(prediction_time)
            prediction_time += interval

        # Add a final snapshot when a valid delivery scan
        # becomes available after the regular schedule.
        event_matches = eta_data["events"].get(shipment_id)

        if event_matches is not None:

            delivery_events = event_matches[
                (event_matches["event_type"] == "DELIVERED")
                & (event_matches["event_status"] == "VALID")
                & (event_matches["event_time"] <= cutoff_time)
                & (event_matches["ingestion_time"] <= cutoff_time)
            ]

            if not delivery_events.empty:

                delivery_event = delivery_events.sort_values(
                    ["event_time", "ingestion_time"]
                ).iloc[-1]

                delivery_ingestion_time = delivery_event[
                    "ingestion_time"
                ]

                if (
                    start_time <= delivery_ingestion_time <= cutoff_time
                    and delivery_ingestion_time not in prediction_times
                ):
                    prediction_times.append(delivery_ingestion_time)

        prediction_times = sorted(set(prediction_times))

        for prediction_time in prediction_times:

            try:
                result = estimate_shipment_eta(
                    shipment_id,
                    prediction_time,
                    _data=eta_data
                )

                result["actual_delivery_at"] = (
                    shipment["actual_delivery_at"].isoformat()
                    if pd.notna(shipment["actual_delivery_at"])
                    else None
                )

                result["actual_shipment_status"] = status

                snapshots.append(result)

            except (ValueError, KeyError) as error:
                print(
                    f"Skipping {shipment_id} at "
                    f"{prediction_time}: {error}"
                )

        if (index + 1) % 100 == 0:
            print(
                f"Processed {index + 1}/{len(shipments)} shipments. "
                f"Snapshots: {len(snapshots)}"
            )

    snapshots_df = pd.DataFrame(snapshots)

    output_path = DATA_DIR / "eta_snapshots.csv"

    snapshots_df.to_csv(output_path, index=False)

    print("\nETA snapshot generation completed.")
    print(f"Total snapshots: {len(snapshots_df)}")
    print(f"Skipped shipments: {skipped_shipments}")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    generate_eta_snapshots()

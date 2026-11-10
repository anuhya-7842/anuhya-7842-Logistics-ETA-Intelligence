
# Data Source Manifest

## 1. Overview

The Logistics ETA Intelligence Platform uses synthetically generated datasets to simulate a logistics network.

The datasets represent shipments, carriers, facilities, routes, tracking events, facility congestion, weather disruptions, service levels, and route modifications.

No external customer, carrier, or logistics company data is used.

## 2. Data Source Details

| Dataset | Source | Description |
|---|---|---|
| carriers.csv | Synthetic generator | Carrier information and operating schedules |
| facilities.csv | Synthetic generator | Facility locations and operating schedules |
| routes.csv | Synthetic generator | Route connections, distances, and transport modes |
| service_levels.csv | Synthetic generator | Delivery targets and grace periods |
| shipments.csv | Synthetic generator | Shipment details and delivery information |
| shipment_legs.csv | Synthetic generator | Individual shipment journey segments |
| tracking_events.csv | Synthetic generator | Carrier tracking scans and event timestamps |
| facility_queues.csv | Synthetic generator | Facility queue and congestion snapshots |
| weather_events.csv | Synthetic generator | Weather disruption windows and estimated impacts |
| ground_truth.csv | Synthetic generator | Final shipment outcomes and delay labels |
| route_changes.csv | Synthetic generator | Shipment route modification records |
| route_change_segments.csv | Synthetic generator | Replacement route segments |

## 3. Generation Configuration

| Parameter | Value |
|---|---|
| Generation method | Python-based synthetic data generation |
| Random seed | 20261022 |
| ID year | 2026 |
| Starter shipment count | 1,000 |
| Target full shipment count | 50,000 |
| Target full tracking event count | 300,000 |
| Target full facility count | 100 |
| Target full disruption window count | 1,000 |
| Timestamp standard | UTC |

The random seed is fixed to support reproducibility.

## 4. Generation Process

The dataset generation pipeline follows these stages:

1. Generate master data for carriers, facilities, routes, and service levels.
2. Generate shipments and shipment legs.
3. Generate delivery outcomes and ground-truth labels.
4. Generate carrier tracking events.
5. Generate route changes and replacement route segments.
6. Generate facility queue snapshots.
7. Generate weather disruption events.

Run the generator from the project root:

```powershell
python -m src.generator
```

## 5. Data Quality and Traceability

The generated datasets include:

- Unique identifiers for entities and operational records.
- Foreign key relationships between related datasets.
- Event occurrence and ingestion timestamps.
- Explicit duplicate tracking event indicators.
- Route change reasons and effective timestamps.
- Weather disruption start and end timestamps.
- Separate ground-truth labels for outcome evaluation.

The ETA engine uses only information available at the prediction timestamp to reduce temporal data leakage.

## 6. Limitations

- All records are synthetic and do not represent actual shipments.
- Carrier performance and facility congestion are simulated.
- Weather events are generated for testing disruption scenarios.
- Generated delivery outcomes are simulated rather than obtained from real logistics operations.
- The current generated dataset contains 1,000 shipments; 50,000 shipments and 300,000 tracking events are target full-scale volumes.

## 7. Reproducibility

To regenerate the datasets:

```powershell
python -m src.generator
```

The fixed random seed is configured in `src/config.py`.

Generated files are stored in the project's `data/` directory.

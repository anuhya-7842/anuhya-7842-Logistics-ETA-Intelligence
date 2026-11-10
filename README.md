
# Logistics ETA Intelligence Platform

An intelligent logistics analytics platform designed to estimate shipment arrival times, identify potential delivery delays, and analyze operational disruptions using shipment tracking events, route information, facility congestion, and weather conditions.

## Project Overview

Logistics operations involve multiple carriers, facilities, transportation routes, and external disruptions. Delayed tracking updates, facility congestion, weather conditions, and route changes can affect shipment delivery schedules.

This platform combines operational logistics data and time-aware ETA calculations to provide shipment-level predictions and delay indicators.

## Key Features

- Synthetic logistics data generation with a fixed random seed.
- Shipment and multi-leg route modeling.
- Carrier tracking event processing.
- Late-arriving and duplicate event handling.
- Facility queue congestion analysis.
- Weather disruption impact analysis.
- Effective-time-aware route change processing.
- Shipment ETA estimation.
- Ground-truth delivery outcome generation.
- Data integrity and business rule validation.
- Automated testing with Pytest.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python 3.10 |
| Data Processing | Pandas |
| Testing | Pytest |
| Data Storage | CSV |
| Version Control | Git, GitHub |

## Project Structure

```text
Logistics ETA Intelligence/
│
├── app.py
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── generator.py
│   ├── business_logic.py
│   ├── eta_engine.py
│   └── validators.py
│
├── data/
│   ├── carriers.csv
│   ├── facilities.csv
│   ├── routes.csv
│   ├── service_levels.csv
│   ├── shipments.csv
│   ├── shipment_legs.csv
│   ├── tracking_events.csv
│   ├── facility_queues.csv
│   ├── weather_events.csv
│   ├── ground_truth.csv
│   ├── route_changes.csv
│   └── route_change_segments.csv
│
├── docs/
│   ├── data_dictionary.md
│   ├── schema.md
│   ├── validation_summary.md
│   └── source_manifest.md
│
├── tests/
│   ├── test_eta_engine.py
│   └── test_validations.py
│
└── scripts/
    └── verify_reproducibility.py
```

## Dataset Overview

The current generated dataset contains:

| Dataset | Records |
|---|---:|
| Carriers | 20 |
| Facilities | 100 |
| Routes | 300 |
| Service Levels | 3 |
| Shipments | 1,000 |
| Shipment Legs | 3,018 |
| Tracking Events | 5,960 |
| Route Changes | 48 |
| Route Change Segments | 96 |
| Facility Queue Snapshots | 120,000 |
| Weather Events | 1,000 |
| Ground Truth Records | 1,000 |

The generator is configured with a fixed random seed of `20261022`.

The target full-scale configuration is 50,000 shipments and 300,000 tracking events. The current dataset is the starter-scale version.

## Installation

### 1. Clone the repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd "Logistics ETA Intelligence"
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

## Generate the Dataset

Run the following command from the project root:

```powershell
python -m src.generator
```

The generated CSV files will be stored in the `data/` directory.

## Run Tests

Execute the automated test suite:

```powershell
python -m pytest -v
```

The current recorded test result is:

```text
18 tests passed successfully using pytest.
```

## ETA Engine

The ETA engine estimates shipment arrival times using:

- Shipment and shipment-leg information.
- Valid tracking events available at prediction time.
- Remaining route distances.
- Facility queue conditions.
- Active weather disruptions.
- Approved route changes effective at prediction time.

The engine excludes duplicate events and prevents future tracking and route-change information from influencing earlier predictions.

## Documentation

Detailed project documentation is available in the `docs/` directory:

- `data_dictionary.md` – Dataset fields and descriptions.
- `schema.md` – Entity relationships and database schema.
- `validation_summary.md` – Data validation checks and test results.
- `source_manifest.md` – Dataset sources and generation details.

## Current Project Status

- [x] Synthetic logistics dataset generation.
- [x] Shipment and route modeling.
- [x] Tracking event generation.
- [x] Facility queue and weather data generation.
- [x] Route change modeling.
- [x] ETA calculation engine.
- [x] Temporal leakage prevention checks.
- [x] Data validation.
- [x] Automated tests.
- [ ] Full-scale dataset generation.
- [ ] Complete application interface and deployment.

## Disclaimer

This project uses synthetic logistics data for development, testing, and demonstration purposes. Predictions and operational metrics do not represent real-world carrier performance.

## Author

Developed as a logistics analytics and ETA intelligence project.

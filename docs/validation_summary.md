
# Data Validation Summary

## 1. Overview

This document summarizes the data quality checks performed on the Logistics ETA Intelligence Platform datasets.

The validation process checks primary keys, foreign keys, relationships, timestamps, data types, business rules, and dataset consistency.

## 2. Validation Environment

| Item | Value |
|---|---|
| Language | Python 3.10.11 |
| Data Processing | Pandas |
| Testing Framework | Pytest |
| Random Seed | 20261022 |
| Generated Shipments | 1,000 |
| Generated Facilities | 100 |
| Generated Tracking Events | 5,960 |
| Generated Weather Events | 1,000 |

## 3. Dataset Validation

| Dataset | Validation Checks |
|---|---|
| Carriers | Unique IDs, valid carrier attributes |
| Facilities | Unique IDs, valid facility attributes |
| Routes | Unique IDs, valid facility references |
| Service Levels | Unique IDs, valid delivery targets |
| Shipments | Unique IDs, valid foreign keys, shipment status |
| Shipment Legs | Unique IDs, valid shipment and route references, leg sequence |
| Tracking Events | Unique IDs, valid foreign keys, event types, timestamps |
| Facility Queues | Unique IDs, valid facility references, non-negative queue metrics |
| Weather Events | Unique IDs, valid references, disruption time ranges |
| Ground Truth | Valid shipment references, delivery labels and outcomes |
| Route Changes | Valid shipment, leg and original route references |
| Route Change Segments | Valid route references, connected replacement segments |

## 4. Tracking Event Quality

Tracking event validation includes:

- Primary key uniqueness.
- Shipment, leg, and facility foreign key checks.
- Valid event types.
- Event timestamp validation.
- Event and shipment-leg facility relationship checks.
- Identification of late-arriving events.
- Identification of duplicate carrier submissions.

Generated tracking event statistics:

| Metric | Count |
|---|---:|
| Total tracking events | 5,960 |
| Valid events | 5,820 |
| Duplicate events | 140 |
| Late-arriving events | 6,036 |

Duplicate events are retained in the dataset with `event_status = DUPLICATE` rather than silently removed.

## 5. Route Change Validation

Route change validation checks:

- Unique route change and segment IDs.
- Valid shipment and shipment leg references.
- Valid original and replacement route references.
- Exactly two replacement segments per route change.
- Correct segment sequence.
- Continuous replacement route connectivity.
- Matching original and replacement route endpoints.

Generated route change statistics:

| Metric | Count |
|---|---:|
| Route changes | 48 |
| Replacement segments | 96 |

## 6. ETA Temporal Validation

The ETA engine follows prediction-time constraints:

- Tracking events are considered only when both event time and ingestion time are at or before the prediction timestamp.
- Duplicate tracking events are excluded from ETA calculations.
- Future route changes are not applied before their effective timestamp.
- Facility queue snapshots are selected using the prediction timestamp.
- Weather disruptions are considered according to their active time windows.

These rules help prevent future information from leaking into historical ETA predictions.

## 7. Automated Test Results

The automated test suite includes:

### ETA Engine Tests

- Late-arriving delivery scans are not used before ingestion.
- Delivery scans are used after ingestion.
- Normal shipments return valid ETA predictions.
- Unknown shipment IDs raise an error.
- Future route changes are not applied early.
- Approved route changes are applied after their effective time.

### Data Validation Tests

- Master data validation.
- Shipment validation.
- Tracking event validation.
- Facility queue validation.
- Weather event validation.
- Delivery outcome validation.
- Route change validation.

Latest recorded test execution:

```text
python -m pytest -v

18 tests passed
```

## 8. Summary

The generated datasets pass the implemented validation checks and the automated test suite.

The validation process helps ensure referential integrity, operational consistency, reproducible data generation, and temporal correctness for the Logistics ETA Intelligence Platform.

## Reproducibility Verification

The reproducibility script was executed successfully.

- Random seed: `20261022`
- Generator executions: 2
- CSV files compared: 12
- Comparison method: SHA-256 checksums
- Result: PASS — all generated CSV files produced identical checksums across both runs.

The complete test suite was also executed after regeneration.

- Total tests: 18
- Passed: 18
- Failed: 0

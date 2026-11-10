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
| Generated Shipments | 50,000 |
| Generated Facilities | 100 |
| Generated Tracking Events | 295,876 |
| Generated Weather Events | 1,000 |

## 3. Full-Scale Dataset Statistics

| Dataset | Records |
|---|---:|
| Carriers | 20 |
| Facilities | 100 |
| Routes | 9,900 |
| Service Levels | 3 |
| Shipments | 50,000 |
| Shipment Legs | 149,964 |
| Tracking Events | 295,876 |
| Route Changes | 1,583 |
| Route Change Segments | 3,166 |
| Facility Queue Snapshots | 120,000 |
| Weather Events | 1,000 |
| Ground Truth Records | 50,000 |

The configured tracking-event generation target is 300,000. The generated dataset currently contains 295,876 events.

## 4. Dataset Validation

The following validation groups were executed:

- **Master Data:** Primary keys, foreign keys, route facilities, and carrier statuses.
- **Shipments:** Primary keys, foreign keys, shipment legs, route relationships, and leg sequence.
- **Tracking Events:** Primary keys, foreign keys, event types, timestamps, facility relationships, and duplicate-event consistency.
- **Facility Queues:** Primary keys, facility references, metric ranges, and timestamps.
- **Weather Events:** Primary keys, target references, severity, disruption windows, and delay impact.
- **Delivery Outcomes:** Shipment coverage, statuses, timestamps, SLA labels, and valid outcome values.
- **Route Changes:** Primary keys, foreign keys, replacement segment counts, segment connectivity, and alternative route endpoints.

## 5. Tracking Event Quality

Tracking event validation includes:

- Primary key uniqueness.
- Shipment, leg, and facility foreign key checks.
- Valid event types.
- Event timestamp validation.
- Event and shipment-leg facility relationship checks.
- Duplicate carrier submission identification.
- Consistency between delivery events and shipment outcomes.

### Generated Tracking Event Statistics

| Metric | Count |
|---|---:|
| Total tracking events | 295,876 |
| Valid events | 289,862 |
| Duplicate events | 6,014 |

Duplicate events are retained in the dataset with `event_status = DUPLICATE` rather than silently removed.

## 6. Route Change Validation

Route change validation checks:

- Unique route change and segment IDs.
- Valid shipment and shipment leg references.
- Valid original and replacement route references.
- Exactly two replacement segments per route change.
- Correct segment sequence.
- Continuous replacement route connectivity.
- Matching original and replacement route endpoints.

### Generated Route Change Statistics

| Metric | Count |
|---|---:|
| Route changes | 1,583 |
| Replacement segments | 3,166 |

## 7. ETA Temporal Validation

The ETA engine follows prediction-time constraints:

- Tracking events are considered only when both event time and ingestion time are at or before the prediction timestamp.
- Duplicate tracking events are excluded from ETA calculations.
- Future route changes are not applied before their effective timestamp.
- Facility queue snapshots are selected using the prediction timestamp.
- Weather disruptions are considered according to their active time windows.

These rules help prevent future information from leaking into historical ETA predictions.

## 8. Automated Test Results

The automated test suite includes ETA engine, snapshot generation, API, anomaly detection, and data validation tests.

The full-scale data validation command was executed:

```text
python -m src.validators
```

Result:

```text
ALL DATA VALIDATIONS PASSED
7 validation groups passed
```

The full regression test suite is still under investigation. Four tests reported failures during the latest full-scale execution. The test run was interrupted before completion.

Therefore, the full-scale regression suite is not reported as passing.

## 9. Reproducibility

The generator uses a fixed random seed of `20261022` to support reproducible data generation.

Full-scale data validation was completed successfully. A complete full-scale reproducibility comparison has not been verified for this dataset.

## 10. Summary

The full-scale dataset contains 50,000 shipments, 149,964 shipment legs, and 295,876 tracking events.

All seven implemented data validation groups passed successfully.

The platform includes data integrity checks, operational business rules, duplicate event handling, route change validation, and temporal constraints for historical ETA predictions.

The automated regression test suite remains under investigation, and its results are reported transparently.


# Logistics ETA Intelligence Platform

## Data Dictionary

This document defines the datasets, fields, relationships, and validation rules used in the Logistics ETA Intelligence Platform.

All generated datasets are stored as CSV files in the `data/` directory.

## 1. Shipment (`shipments.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| shipment_id | String | Yes | Unique PK, SHP-2026-000001 format |
| customer_id | String | Yes | Non-empty customer reference |
| origin_facility_id | String | Yes | Facility FK |
| destination_facility_id | String | Yes | Facility FK |
| carrier_id | String | Yes | Carrier FK |
| service_level_id | String | Yes | ServiceLevel FK |
| created_at | Datetime | Yes | Valid UTC timestamp |
| promised_delivery_at | Datetime | Yes | After created_at |
| actual_delivery_at | Datetime | No | Populated for delivered or delayed shipments |
| status | Enum | Yes | CREATED, PICKED_UP, IN_TRANSIT, AT_FACILITY, OUT_FOR_DELIVERY, DELIVERED, DELAYED, CANCELLED |
| current_eta | Datetime | No | Valid UTC timestamp |

## 2. Shipment Leg (`shipment_legs.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| leg_id | String | Yes | Unique PK |
| shipment_id | String | Yes | Shipment FK |
| route_id | String | Yes | Route FK |
| carrier_id | String | Yes | Carrier FK |
| origin_facility_id | String | Yes | Facility FK |
| destination_facility_id | String | Yes | Facility FK |
| leg_sequence | Integer | Yes | Continuous sequence starting at 1 |
| planned_departure | Datetime | Yes | Before planned arrival |
| planned_arrival | Datetime | Yes | After planned departure |
| actual_departure | Datetime | No | Valid actual timestamp |
| actual_arrival | Datetime | No | Valid actual timestamp |

## 3. Carrier (`carriers.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| carrier_id | String | Yes | Unique PK |
| carrier_name | String | Yes | Non-empty |
| carrier_type | Enum | Yes | ROAD, AIR, RAIL, SEA |
| operating_status | Enum | Yes | ACTIVE, INACTIVE |
| service_rating | Float | Yes | Between 1 and 5 |
| operating_days | String | Yes | Valid operating-day schedule |
| operating_start_hour | Integer | Yes | Valid hour |
| operating_end_hour | Integer | Yes | Valid hour |

## 4. Facility (`facilities.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| facility_id | String | Yes | Unique PK |
| facility_name | String | Yes | Non-empty |
| city | String | Yes | Non-empty |
| country | String | Yes | Non-empty |
| facility_type | Enum | Yes | WAREHOUSE, HUB, PORT |
| timezone | String | Yes | Valid timezone |
| operating_hours | String | Yes | Valid operating schedule |
| operating_days | String | Yes | Valid operating-day schedule |
| operating_start_hour | Integer | Yes | Valid hour |
| operating_end_hour | Integer | Yes | Valid hour |

## 5. Route (`routes.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| route_id | String | Yes | Unique PK |
| origin_facility_id | String | Yes | Facility FK |
| destination_facility_id | String | Yes | Facility FK |
| distance_km | Float | Yes | Greater than zero |
| transport_mode | Enum | Yes | ROAD, AIR, RAIL, SEA |
| route_status | Enum | Yes | ACTIVE, INACTIVE |

## 6. Tracking Event (`tracking_events.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| event_id | String | Yes | Unique PK |
| shipment_id | String | Yes | Shipment FK |
| leg_id | String | Yes | ShipmentLeg FK |
| facility_id | String | Yes | Facility FK |
| event_type | Enum | Yes | DEPARTED_FACILITY, ARRIVED_FACILITY, DELIVERED |
| event_time | Datetime | Yes | Actual event occurrence time |
| ingestion_time | Datetime | Yes | System receipt time, not earlier than event_time |
| event_status | Enum | Yes | VALID, DUPLICATE |
| source | String | Yes | Non-empty event source |

Duplicate events retain their original event details but have separate event IDs and later ingestion timestamps.

Only VALID events available by the prediction timestamp are considered by the ETA engine.

## 7. Facility Queue (`facility_queues.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| queue_id | String | Yes | Unique PK |
| facility_id | String | Yes | Facility FK |
| snapshot_time | Datetime | Yes | Valid UTC snapshot timestamp |
| queued_shipments | Integer | Yes | Zero or greater |
| average_wait_minutes | Float | Yes | Zero or greater |
| capacity_utilization_pct | Float | Yes | Between 0 and 100 |
| queue_status | Enum | Yes | Valid queue status |

Queue records represent time-based facility congestion snapshots.

## 8. Weather Event (`weather_events.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| weather_event_id | String | Yes | Unique PK |
| facility_id | String | Conditional | Facility FK when facility-targeted |
| route_id | String | Conditional | Route FK when route-targeted |
| weather_type | Enum | Yes | HEAVY_RAIN, FLOOD, STORM, FOG, EXTREME_HEAT, STRONG_WINDS |
| severity | Enum | Yes | LOW, MEDIUM, HIGH, CRITICAL |
| start_time | Datetime | Yes | Before end_time |
| end_time | Datetime | Yes | After start_time |
| delay_impact_minutes | Integer | Yes | Zero or greater |
| source | String | Yes | Non-empty source |

Exactly one disruption target is specified: a facility or a route.

## 9. Service Level (`service_levels.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| service_level_id | String | Yes | Unique PK |
| service_name | String | Yes | Non-empty |
| target_delivery_hours | Integer | Yes | Greater than zero |
| delay_grace_hours | Integer | Yes | Zero or greater |
| effective_from | Datetime | Yes | Valid effective start |
| effective_to | Datetime | No | After effective_from |

Service-level grace periods are used to derive delivery delay labels.

## 10. Ground Truth (`ground_truth.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| shipment_id | String | Yes | Unique PK and Shipment FK |
| promised_delivery_at | Datetime | Yes | Valid promised timestamp |
| actual_delivery_at | Datetime | Conditional | Required for DELIVERED and DELAYED |
| delay_minutes | Integer | Conditional | Zero or greater |
| grace_minutes | Integer | Yes | Zero or greater |
| is_late | Integer | Conditional | 0 or 1; null for unknown or cancelled |
| delay_label | Enum | Yes | ON_TIME, LATE, UNKNOWN, CANCELLED |
| final_status | Enum | Yes | DELIVERED, DELAYED, IN_TRANSIT, CANCELLED |

Ground-truth labels are generated separately from operational tracking events and must not be used as prediction-time input features.

## 11. Route Change (`route_changes.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| route_change_id | String | Yes | Unique PK, RCH-2026-000001 format |
| shipment_id | String | Yes | Shipment FK |
| leg_id | String | Yes | ShipmentLeg FK |
| original_route_id | String | Yes | Original Route FK |
| change_time | Datetime | Yes | Valid UTC effective timestamp |
| reason | Enum | Yes | WEATHER_DISRUPTION, FACILITY_CONGESTION, ROAD_CLOSURE, OPERATIONAL_OPTIMIZATION |
| change_status | Enum | Yes | APPROVED |
| source | String | Yes | Non-empty source |

An approved route change becomes effective only at or after its change_time.

## 12. Route Change Segment (`route_change_segments.csv`)

| Field | Type | Required | Validation |
|---|---|---|---|
| segment_id | String | Yes | Unique PK |
| route_change_id | String | Yes | RouteChange FK |
| segment_sequence | Integer | Yes | Continuous sequence starting at 1 |
| route_id | String | Yes | Replacement Route FK |
| origin_facility_id | String | Yes | Facility FK |
| destination_facility_id | String | Yes | Facility FK |
| distance_km | Float | Yes | Greater than zero |
| transport_mode | Enum | Yes | ROAD, AIR, RAIL, SEA |

Each generated route change contains two replacement segments. The first segment's destination must match the second segment's origin. The complete replacement path must preserve the original leg's endpoints.

## 13. Relationships

- Carrier 1:N Shipment
- Carrier 1:N ShipmentLeg
- Shipment 1:N ShipmentLeg
- Shipment 1:N TrackingEvent
- Shipment 1:1 GroundTruth
- Shipment 1:N RouteChange
- Route 1:N ShipmentLeg
- Route 1:N WeatherEvent
- Route 1:N RouteChangeSegment
- Facility 1:N ShipmentLeg
- Facility 1:N TrackingEvent
- Facility 1:N FacilityQueue
- Facility 1:N WeatherEvent
- ServiceLevel 1:N Shipment
- RouteChange 1:N RouteChangeSegment

## 14. Data Generation Standards

- Fixed random seed: `20261022`
- Primary keys must be unique.
- Foreign keys must reference existing parent records.
- Event time and ingestion time must remain separate.
- Historical tracking events must not be overwritten.
- Duplicate events must remain identifiable.
- Ground-truth labels must be stored separately from operational data.
- Derived values must be calculated from source records.
- Future events and future route changes must not influence historical ETA predictions.
- Approved route changes must be applied only after their effective timestamps.
- All stored timestamps use UTC.
- Data generation must be reproducible using the fixed random seed.

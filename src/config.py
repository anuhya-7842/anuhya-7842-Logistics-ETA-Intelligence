
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"

# Reproducibility
RANDOM_SEED = 20261022

# Dataset configuration
DATA_CONFIG = {
    "shipments": 50_000,
    "tracking_events": 300_000,
    "facilities": 100,
    "disruption_windows": 1_000,
}

# Starter dataset for development and testing
STARTER_CONFIG = {
    "shipments": 1_000,
    "facilities": 20,
    "disruption_windows": 50,
}

# Full dataset
FULL_CONFIG = DATA_CONFIG

# ID configuration
ID_YEAR = 2026

# Shipment statuses
SHIPMENT_STATUSES = [
    "CREATED",
    "PICKED_UP",
    "IN_TRANSIT",
    "AT_FACILITY",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "DELAYED",
    "CANCELLED",
]

# Delay categories
DELAY_CATEGORIES = [
    "WEATHER",
    "FACILITY_CONGESTION",
    "CARRIER_DELAY",
    "ROUTE_DISRUPTION",
    "LATE_SCAN",
    "UNKNOWN",
]

# ETA configuration
ETA_SNAPSHOT_INTERVAL_HOURS = 6

# Default timezone
DEFAULT_TIMEZONE = "UTC"

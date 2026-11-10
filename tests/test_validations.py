
from src.validators import (
    validate_master_data,
    validate_shipments,
    validate_tracking_events,
    validate_facility_queues,
    validate_weather_events,
    validate_delivery_outcomes,
    validate_route_changes,
)


def test_master_data():
    validate_master_data()


def test_shipments():
    validate_shipments()


def test_tracking_events():
    validate_tracking_events()


def test_facility_queues():
    validate_facility_queues()


def test_weather_events():
    validate_weather_events()


def test_delivery_outcomes():
    validate_delivery_outcomes()


def test_route_changes():
    validate_route_changes()

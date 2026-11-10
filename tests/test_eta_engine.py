import pytest

from src.eta_engine import estimate_shipment_eta


def test_late_arriving_delivery_scan_is_not_used_early():

    result = estimate_shipment_eta(
        "SHP-2026-000001",
        "2026-04-02T06:00:00Z"
    )

    assert result["status"] == "POTENTIALLY_OVERDUE_NO_SCAN"
    assert result["delay_reason"] == "MISSING_ARRIVAL_SCAN"
    assert result["predicted_eta"] is None
    assert result["overdue_minutes"] == 1380.0


def test_delivery_scan_is_used_after_ingestion():

    result = estimate_shipment_eta(
        "SHP-2026-000001",
        "2026-04-02T08:00:00Z"
    )

    assert result["status"] == "DELIVERED"

    assert result["predicted_eta"] == (
        "2026-04-02T04:46:00+00:00"
    )

    assert result["delay_reason"] is None


def test_normal_shipment_returns_valid_prediction():

    result = estimate_shipment_eta(
        "SHP-2026-000002",
        "2026-02-24T23:30:00Z"
    )

    assert result["shipment_id"] == "SHP-2026-000002"

    assert result["status"] in [
        "IN_TRANSIT",
        "DELIVERED",
        "POTENTIALLY_OVERDUE_NO_SCAN",
        "NO_REMAINING_LEGS"
    ]


def test_unknown_shipment_raises_error():

    with pytest.raises(ValueError, match="Shipment not found"):
        estimate_shipment_eta(
            "SHP-9999-999999",
            "2026-01-30T12:00:00Z"
        )


def test_future_route_change_is_not_applied_early():

    result = estimate_shipment_eta(
        "SHP-2026-019262",
        "2026-08-05T20:00:00Z"
    )

    assert result["route_changes_applied"] == []


def test_approved_route_change_is_applied_after_effective_time():

    result = estimate_shipment_eta(
        "SHP-2026-019262",
        "2026-08-05T21:30:00Z"
    )

    assert "RCH-2026-000001" in result["route_changes_applied"]
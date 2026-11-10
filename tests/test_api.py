
from app import app


def test_home_endpoint():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json["status"] == "running"


def test_health_endpoint():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_valid_shipment_eta_endpoint():
    client = app.test_client()

    response = client.get(
        "/api/shipments/SHP-2026-000010/eta"
    )

    assert response.status_code == 200

    result = response.json

    assert result["shipment_id"] == "SHP-2026-000010"
    assert "predicted_eta" in result
    assert "base_travel_minutes" in result
    assert "queue_delay_minutes" in result
    assert "weather_delay_minutes" in result


def test_unknown_shipment_endpoint():
    client = app.test_client()

    response = client.get(
        "/api/shipments/SHP-999999/eta"
    )

    assert response.status_code == 404
    assert "Shipment not found" in response.json["error"]


def test_historical_eta_prediction():
    client = app.test_client()

    response = client.get(
        "/api/shipments/SHP-2026-000010/eta",
        query_string={
            "as_of": "2026-11-10T07:00:00Z"
        }
    )

    assert response.status_code == 200
    assert response.json["prediction_time"] == (
        "2026-11-10T07:00:00+00:00"
    )

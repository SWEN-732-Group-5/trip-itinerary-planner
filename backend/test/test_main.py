from fastapi.testclient import TestClient

from src.main import app


def test_booking_summary_success():
    with TestClient(app) as client:
        # user1 has two bookings
        response = client.get("/booking-summary/user1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        references = sorted([entry["reference_number"] for entry in data])
        assert references == ["REF123", "REF456"]
        cs_numbers = sorted([entry["customer_service_number"] for entry in data])
        assert cs_numbers == ["CSN123", "CSN456"]
        provider_names = sorted([entry["provider_name"] for entry in data])
        assert provider_names == ["Provider A", "Provider B"]

        # user2 has one booking
        response = client.get("/booking-summary/user2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["reference_number"] == "REF789"
        assert data[0]["provider_name"] == "Provider C"

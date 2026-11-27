from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "payment"}


def test_create_payment():
    response = client.post(
        "/payments",
        json={
            "amount_cents": 1250,
            "currency": "USD",
            "reference": "order-123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "payment_id": "demo-order-123",
        "status": "succeeded",
        "amount_cents": 1250,
        "currency": "USD",
        "message": "Simulated payment only; no money was charged.",
    }


def test_create_payment_rejects_non_positive_amount():
    response = client.post(
        "/payments",
        json={
            "amount_cents": 0,
            "currency": "USD",
            "reference": "order-123",
        },
    )

    assert response.status_code == 422

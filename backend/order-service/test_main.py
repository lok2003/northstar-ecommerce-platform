from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from main import app


client = TestClient(app)


def setup_function():
    main.orders.clear()


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "orders"}


def test_create_order():
    class FakePaymentResponse:
        is_error = False

        def json(self):
            return {
                "payment_id": "demo-order",
                "status": "succeeded",
            }

    payment_response = FakePaymentResponse()

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url, json):
            assert url.endswith("/payments")
            assert json["amount_cents"] == 2300
            assert json["currency"] == "USD"
            return payment_response

    with patch.object(main.httpx, "AsyncClient", return_value=FakeAsyncClient()):
        response = client.post(
            "/orders",
            json={
                "username": "lokesh",
                "items": [
                    {
                        "product_id": 1,
                        "name": "Everyday Runner",
                        "quantity": 2,
                        "unit_price_cents": 890,
                    },
                    {
                        "product_id": 2,
                        "name": "Cap",
                        "quantity": 1,
                        "unit_price_cents": 520,
                    },
                ],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "lokesh"
    assert body["total_cents"] == 2300
    assert body["status"] == "paid"
    assert body["payment"]["status"] == "succeeded"
    assert len(main.orders) == 1


def test_create_order_rejects_empty_items():
    response = client.post(
        "/orders",
        json={"username": "lokesh", "items": []},
    )

    assert response.status_code == 422

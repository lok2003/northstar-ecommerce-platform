from fastapi.testclient import TestClient

import main
from main import app


client = TestClient(app)
CART_ID = "123e4567-e89b-12d3-a456-426614174000"


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gateway"}


def test_register_forwards_credentials(monkeypatch):
    async def fake_call_service(base_url, path, **kwargs):
        assert path == "/register"
        assert kwargs["payload"] == {
            "username": "lokesh",
            "password": "password123",
        }
        return {"message": "registered"}

    monkeypatch.setattr(main, "call_service", fake_call_service)

    response = client.post(
        "/api/auth/register",
        json={"username": "lokesh", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "registered"}


def test_products_forwards_request(monkeypatch):
    async def fake_call_service(base_url, path, **kwargs):
        assert path == "/products"
        return [{"id": 1, "name": "Everyday Runner"}]

    monkeypatch.setattr(main, "call_service", fake_call_service)

    response = client.get("/api/products")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Everyday Runner"


def test_get_cart_requires_valid_cart_id():
    missing = client.get("/api/cart")
    assert missing.status_code == 400
    assert missing.json() == {"detail": "X-Cart-Id header required"}

    invalid = client.get("/api/cart", headers={"X-Cart-Id": "not-a-uuid"})
    assert invalid.status_code == 400
    assert invalid.json() == {"detail": "Invalid cart ID"}


def test_add_cart_item(monkeypatch):
    async def fake_call_service(base_url, path, **kwargs):
        assert path == f"/carts/{CART_ID}/items"
        assert kwargs["payload"] == {"product_id": 1, "quantity": 2}
        return {"items": [{"product_id": 1, "quantity": 2}]}

    monkeypatch.setattr(main, "call_service", fake_call_service)

    response = client.post(
        "/api/cart/items",
        headers={"X-Cart-Id": CART_ID},
        json={"product_id": 1, "quantity": 2},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 2


def test_checkout_rejects_empty_cart(monkeypatch):
    async def fake_call_service(base_url, path, **kwargs):
        if path == "/verify":
            return {"username": "lokesh"}
        if path == f"/carts/{CART_ID}":
            return {"items": []}
        raise AssertionError(f"Unexpected call: {path}")

    monkeypatch.setattr(main, "call_service", fake_call_service)

    response = client.post(
        "/api/checkout",
        headers={
            "Authorization": "Bearer valid",
            "X-Cart-Id": CART_ID,
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Your cart is empty"}


def test_checkout_creates_order_and_clears_cart(monkeypatch):
    calls = []

    async def fake_call_service(base_url, path, **kwargs):
        calls.append((path, kwargs))
        if path == "/verify":
            return {"username": "lokesh"}
        if path == f"/carts/{CART_ID}":
            return {"items": [{"product_id": 1, "quantity": 2}]}
        if path == "/products":
            return [
                {
                    "id": 1,
                    "name": "Everyday Runner",
                    "price_cents": 8900,
                }
            ]
        if path == "/orders":
            return {"order_id": "order-1", "status": "paid"}
        if path == f"/carts/{CART_ID}" and kwargs.get("method") == "DELETE":
            return None
        raise AssertionError(f"Unexpected call: {path} {kwargs}")

    monkeypatch.setattr(main, "call_service", fake_call_service)

    response = client.post(
        "/api/checkout",
        headers={
            "Authorization": "Bearer valid",
            "X-Cart-Id": CART_ID,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"order_id": "order-1", "status": "paid"}
    assert any(
        path == f"/carts/{CART_ID}" and kwargs.get("method") == "DELETE"
        for path, kwargs in calls
    )

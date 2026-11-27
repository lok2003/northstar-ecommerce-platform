from fastapi.testclient import TestClient

import main
from main import app


client = TestClient(app)


def setup_function():
    main.carts.clear()


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cart"}


def test_empty_cart():
    response = client.get("/carts/abc")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_add_update_and_remove_item():
    cart_id = "cart-1"

    added = client.post(
        f"/carts/{cart_id}/items",
        json={"product_id": 2, "quantity": 3},
    )
    assert added.status_code == 200
    assert added.json() == {"items": [{"product_id": 2, "quantity": 3}]}

    updated = client.put(
        f"/carts/{cart_id}/items/2",
        json={"quantity": 5},
    )
    assert updated.status_code == 200
    assert updated.json() == {"items": [{"product_id": 2, "quantity": 5}]}

    removed = client.delete(f"/carts/{cart_id}/items/2")
    assert removed.status_code == 204
    assert client.get(f"/carts/{cart_id}").json() == {"items": []}


def test_add_item_rejects_quantity_above_maximum():
    client.post(
        "/carts/cart-1/items",
        json={"product_id": 1, "quantity": 95},
    )
    response = client.post(
        "/carts/cart-1/items",
        json={"product_id": 1, "quantity": 5},
    )

    assert response.status_code == 422


def test_update_missing_item():
    response = client.put(
        "/carts/missing/items/99",
        json={"quantity": 2},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Cart item not found"}


def test_clear_cart():
    client.post(
        "/carts/cart-1/items",
        json={"product_id": 1, "quantity": 1},
    )

    response = client.delete("/carts/cart-1")

    assert response.status_code == 204
    assert client.get("/carts/cart-1").json() == {"items": []}

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "catalog"}


def test_get_products():
    response = client.get("/products")

    assert response.status_code == 200
    products = response.json()
    assert len(products) == 6
    assert products[0]["id"] == 1
    assert products[0]["name"] == "Everyday Runner"

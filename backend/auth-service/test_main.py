from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "auth"
    }

def test_register_user():
    response = client.post(
        "/register",
        json={
            "username": "lokesh",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert response.json() == {"message": "registered"}

def test_register_duplicate_user():
    client.post(
        "/register",
        json={
            "username": "lokesh",
            "password": "password123"
        }
    )

    response = client.post(
        "/register",
        json={
            "username": "lokesh",
            "password": "password123"
        }
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Username already exists"
    }

def test_register_short_password():
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "password": "123"
        }
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Password must be at least 8 characters"
    }

def test_login_user():
    client.post(
        "/register",
        json={
            "username": "loginuser",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        json={
            "username": "loginuser",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_password():
    client.post(
        "/register",
        json={
            "username": "wrongpassuser",
            "password": "password123"
        }
    )

    response = client.post(
        "/login",
        json={
            "username": "wrongpassuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid username or password"
    }

def test_verify_token():
    client.post(
        "/register",
        json={
            "username": "verifyuser",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/login",
        json={
            "username": "verifyuser",
            "password": "password123"
        }
    )

    token = login_response.json()["token"]

    response = client.post(
        "/verify",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json() == {"username": "verifyuser"}

def test_verify_invalid_token():
    response = client.post(
        "/verify",
        headers={
            "Authorization": "Bearer invalid-token"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token"
    }

def test_verify_missing_token():
    response = client.post("/verify")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Bearer token required"
    }
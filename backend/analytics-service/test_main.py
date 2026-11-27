from fastapi.testclient import TestClient

import main
from main import app


client = TestClient(app)


def setup_function():
    main.registrations = 0
    main.scores.clear()


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "analytics"}


def test_record_registration_and_quiz_scores():
    registration = client.post(
        "/events",
        json={"kind": "registration", "username": "lokesh"},
    )
    assert registration.status_code == 200
    assert registration.json() == {"status": "recorded"}

    client.post("/events", json={"kind": "quiz_submission", "score": 100})
    client.post("/events", json={"kind": "quiz_submission", "score": 50})

    response = client.get("/analytics")

    assert response.status_code == 200
    assert response.json() == {
        "users": 1,
        "quizzesCompleted": 2,
        "avgScore": 75.0,
    }


def test_empty_analytics():
    response = client.get("/analytics")

    assert response.status_code == 200
    assert response.json() == {
        "users": 0,
        "quizzesCompleted": 0,
        "avgScore": 0,
    }

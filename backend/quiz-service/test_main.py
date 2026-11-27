from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "quiz"}


def test_get_quiz_hides_answers():
    response = client.get("/quiz")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "question": "What is Kubernetes?"}
    ]


def test_submit_correct_answer():
    response = client.post(
        "/quiz/submit",
        json={"quiz_id": 1, "answer": "  Container Orchestration Platform  "},
    )

    assert response.status_code == 200
    assert response.json() == {"score": 100, "correct": True}


def test_submit_incorrect_answer():
    response = client.post(
        "/quiz/submit",
        json={"quiz_id": 1, "answer": "A database"},
    )

    assert response.status_code == 200
    assert response.json() == {"score": 0, "correct": False}


def test_submit_unknown_quiz():
    response = client.post(
        "/quiz/submit",
        json={"quiz_id": 999, "answer": "Anything"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Quiz not found"}

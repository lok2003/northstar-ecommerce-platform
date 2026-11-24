from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Quiz Service")
quizzes = [
    {
        "id": 1,
        "question": "What is Kubernetes?",
        "answer": "Container orchestration platform",
    }
]


class Submission(BaseModel):
    quiz_id: int
    answer: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "quiz"}


@app.get("/quiz")
async def get_quiz() -> list[dict[str, int | str]]:
    return [
        {"id": quiz["id"], "question": quiz["question"]}
        for quiz in quizzes
    ]


@app.post("/quiz/submit")
async def submit(data: Submission) -> dict[str, int | bool]:
    quiz = next((item for item in quizzes if item["id"] == data.quiz_id), None)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    correct = data.answer.strip().casefold() == quiz["answer"].casefold()
    return {"score": 100 if correct else 0, "correct": correct}

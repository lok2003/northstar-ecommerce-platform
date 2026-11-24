from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Analytics Service")
registrations = 0
scores: list[int] = []


class Event(BaseModel):
    kind: Literal["registration", "quiz_submission"]
    username: str | None = None
    score: int | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "analytics"}


@app.post("/events")
async def record_event(event: Event) -> dict[str, str]:
    global registrations
    if event.kind == "registration":
        registrations += 1
    elif event.score is not None:
        scores.append(event.score)
    return {"status": "recorded"}


@app.get("/analytics")
async def analytics() -> dict[str, int | float]:
    average_score = sum(scores) / len(scores) if scores else 0
    return {
        "users": registrations,
        "quizzesCompleted": len(scores),
        "avgScore": round(average_score, 1),
    }

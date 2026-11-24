import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Authentication Service")
SECRET = os.getenv("JWT_SECRET", "local-learning-demo-secret")
users: dict[str, str] = {}


class User(BaseModel):
    username: str
    password: str


def hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, _ = stored_hash.split(":", maxsplit=1)
    return secrets.compare_digest(
        hash_password(password, bytes.fromhex(salt_hex)), stored_hash
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth"}


@app.post("/register")
async def register(user: User) -> dict[str, str]:
    if user.username in users:
        raise HTTPException(status_code=409, detail="Username already exists")
    if len(user.password) < 8:
        raise HTTPException(
            status_code=422, detail="Password must be at least 8 characters"
        )
    users[user.username] = hash_password(user.password, secrets.token_bytes(16))
    return {"message": "registered"}


@app.post("/login")
async def login(user: User) -> dict[str, str]:
    stored_hash = users.get(user.username)
    if not stored_hash or not verify_password(user.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = jwt.encode(
        {
            "sub": user.username,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        SECRET,
        algorithm="HS256",
    )
    return {"token": token}


@app.post("/verify")
async def verify_token(
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    username = payload.get("sub")
    if not isinstance(username, str) or username not in users:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"username": username}

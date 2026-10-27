import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Auth Service")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-this-secret")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}


@app.post("/token")
def create_token(body: LoginRequest):
    if body.username != DEMO_USERNAME or body.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": body.username,
        "role": "user",
        "token_type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60,
    }


@app.get("/verify")
def verify_token(authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "token_type"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Do not accept a narrowly scoped Valet Key as a normal API login token.
    if payload.get("token_type") != "access":
        raise HTTPException(status_code=401, detail="Wrong token type")

    return {
        "authenticated": True,
        "username": payload["sub"],
        "role": payload.get("role", "user"),
    }

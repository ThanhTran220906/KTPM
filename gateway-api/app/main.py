import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import jwt
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Gateway Aggregation and Valet Key API")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-this-secret")
JWT_ALGORITHM = "HS256"
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
VALET_KEY_TTL_SECONDS = int(os.getenv("VALET_KEY_TTL_SECONDS", "300"))


def decode_token(authorization: str | None, expected_type: str) -> dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    scheme, sep, token = authorization.partition(" ")
    if not sep or scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "token_type"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("token_type") != expected_type:
        raise HTTPException(status_code=401, detail="Wrong token type")
    return payload


async def get_json(url: str, params: dict | None = None) -> Any:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Backend service unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Backend service error")
    try:
        return response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Backend returned invalid JSON")


@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway-api"}


@app.get("/users/{user_id}/summary")
async def user_summary(
    user_id: int,
    authorization: str | None = Header(default=None),
):
    # Validate the ordinary login access token even though Nginx also performs auth_request.
    decode_token(authorization, "access")

    user, orders = await _get_user_and_orders(user_id)
    if isinstance(orders, dict) and "orders" in orders:
        order_list = orders["orders"]
    else:
        order_list = orders if isinstance(orders, list) else []

    return {
        "user": user,
        "orders": order_list,
        "total_orders": len(order_list),
    }


async def _get_user_and_orders(user_id: int):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            user_response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
            orders_response = await client.get(
                f"{ORDER_SERVICE_URL}/orders",
                params={"user_id": user_id},
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Backend service unavailable")

    if user_response.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    if user_response.status_code >= 400 or orders_response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Backend service error")

    try:
        return user_response.json(), orders_response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Backend returned invalid JSON")


@app.post("/valet-keys/orders/{order_id}")
async def issue_valet_key(
    order_id: int,
    authorization: str | None = Header(default=None),
):
    access_payload = decode_token(authorization, "access")

    # Only issue a key for an order that exists.
    order = await get_json(f"{ORDER_SERVICE_URL}/orders/{order_id}")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=VALET_KEY_TTL_SECONDS)
    token_payload = {
        "sub": access_payload["sub"],
        "token_type": "valet",
        "scope": "order:read",
        "resource": f"order:{order_id}",
        "iat": now,
        "exp": expires_at,
    }
    valet_token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": valet_token,
        "token_type": "Bearer",
        "scope": "order:read",
        "resource": f"order:{order_id}",
        "expires_in": VALET_KEY_TTL_SECONDS,
        "order": order,
    }


@app.get("/valet/orders/{order_id}")
async def read_order_with_valet_key(
    order_id: int,
    authorization: str | None = Header(default=None),
):
    payload = decode_token(authorization, "valet")
    if payload.get("scope") != "order:read":
        raise HTTPException(status_code=403, detail="Insufficient scope")
    if payload.get("resource") != f"order:{order_id}":
        raise HTTPException(status_code=403, detail="Valet key is not valid for this order")

    return await get_json(f"{ORDER_SERVICE_URL}/orders/{order_id}")

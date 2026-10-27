
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from threading import RLock

from fastapi import FastAPI, HTTPException, Query, Request, status

from app.models import Order, OrderCreate

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("order-service")


def seed_orders() -> dict[int, Order]:
    now = datetime.now(timezone.utc)
    records = [
        (1, 1, "Mechanical Keyboard", 1, 79.99, "completed"),
        (2, 1, "USB-C Hub", 1, 39.50, "completed"),
        (3, 1, "Laptop Stand", 2, 49.00, "pending"),
        (4, 2, "Wireless Mouse", 1, 24.99, "completed"),
        (5, 2, "Monitor", 1, 199.00, "processing"),
        (6, 2, "HDMI Cable", 2, 12.50, "completed"),
        (7, 3, "Webcam", 1, 59.00, "completed"),
        (8, 3, "Headphones", 1, 89.99, "pending"),
        (9, 3, "Laptop Sleeve", 1, 29.99, "completed"),
        (10, 1, "Desk Lamp", 1, 34.95, "processing"),
    ]
    return {
        order_id: Order(
            id=order_id,
            user_id=user_id,
            item=item,
            quantity=quantity,
            amount=amount,
            status=order_status,
            created_at=now,
        )
        for (
            order_id,
            user_id,
            item,
            quantity,
            amount,
            order_status,
        ) in records
    }


_orders = seed_orders()
_lock = RLock()
_next_id = max(_orders) + 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting order-service with %d seeded orders", len(_orders))
    yield
    logger.info("Stopping order-service")


app = FastAPI(
    title="Order Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "request_started method=%s path=%s",
        request.method,
        request.url.path,
    )
    response = await call_next(request)
    logger.info(
        "request_completed method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "order-service"}


@app.get("/orders", response_model=list[Order])
async def list_orders(
    user_id: int | None = Query(default=None, gt=0),
) -> list[Order]:
    with _lock:
        orders = [_orders[key] for key in sorted(_orders)]

    if user_id is not None:
        orders = [order for order in orders if order.user_id == user_id]

    return orders


@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int) -> Order:
    with _lock:
        order = _orders.get(order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


@app.post(
    "/orders",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(data: OrderCreate) -> Order:
    global _next_id

    with _lock:
        order = Order(
            id=_next_id,
            user_id=data.user_id,
            item=data.item,
            quantity=data.quantity,
            amount=data.amount,
            status=data.status,
            created_at=datetime.now(timezone.utc),
        )
        _orders[_next_id] = order
        _next_id += 1

    return order

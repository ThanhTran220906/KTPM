
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status

from app.models import User, UserCreate
from app.storage import storage

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("user-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting user-service")
    yield
    logger.info("Stopping user-service")


app = FastAPI(
    title="User Service",
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
    return {"status": "ok", "service": "user-service"}


@app.get("/users", response_model=list[User])
async def list_users() -> list[User]:
    return storage.list_users()


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int) -> User:
    user = storage.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@app.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate) -> User:
    try:
        return storage.create_user(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


from threading import RLock

from app.models import User, UserCreate


class UserStorage:
    """Thread-safe in-memory user store with deterministic seed data."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._users: dict[int, User] = {
            1: User(
                id=1,
                name="Alice Nguyen",
                email="alice@example.com",
                role="user",
            ),
            2: User(
                id=2,
                name="Bob Tran",
                email="bob@example.com",
                role="user",
            ),
            3: User(
                id=3,
                name="Charlie Le",
                email="charlie@example.com",
                role="admin",
            ),
        }
        self._next_id = 4

    def list_users(self) -> list[User]:
        with self._lock:
            return [
                self._users[user_id]
                for user_id in sorted(self._users)
            ]

    def get_user(self, user_id: int) -> User | None:
        with self._lock:
            return self._users.get(user_id)

    def create_user(self, data: UserCreate) -> User:
        with self._lock:
            if any(
                user.email.casefold() == data.email.casefold()
                for user in self._users.values()
            ):
                raise ValueError("A user with this email already exists")

            user = User(
                id=self._next_id,
                name=data.name,
                email=data.email,
                role=data.role,
            )
            self._users[user.id] = user
            self._next_id += 1
            return user


storage = UserStorage()

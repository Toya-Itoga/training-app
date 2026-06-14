"""Authentication service: user lookup, password hashing, JWT issuance.

Token lifetime: JWT_EXPIRE_HOURS (default 6h) per CLAUDE.md.
Auto-creates account on first login if username doesn't exist.
"""
import bcrypt
from ulid import ULID

import repositories.user_repository as user_repo
from utils.auth import create_token
from services.exercise_service import seed_default_exercises


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def login(username: str, password: str) -> str | None:
    """Authenticate user and return a JWT, or None on failure.

    First login auto-creates the account and seeds default exercises.
    """
    user = user_repo.find_by_username(username)

    if user is None:
        # Auto-register on first login
        user_id = str(ULID())
        pw_hash = hash_password(password)
        user = user_repo.create(username, user_id, pw_hash)
        seed_default_exercises(username)
    else:
        if not verify_password(password, user["password"]):
            return None

    return create_token(user["user_id"], username)

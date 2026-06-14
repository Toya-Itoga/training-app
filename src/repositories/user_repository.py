"""User table access layer (DynamoDB).

Schema (config/requirements.md):
  PK: USER#user_name (S)
  SK: user_id        (S)
  Attributes: user_name, user_id, email, password (bcrypt hash)
"""
import os
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from database import from_decimal, get_dynamodb


def _table():
    return get_dynamodb().Table(os.getenv("USER_TABLE_NAME", "users"))


def find_by_username(user_name: str) -> dict | None:
    """Return user item or None if not found."""
    resp = _table().query(
        KeyConditionExpression=Key("PK").eq(f"USER#{user_name}")
    )
    items = resp.get("Items", [])
    return from_decimal(items[0]) if items else None


def create(user_name: str, user_id: str, password_hash: str) -> dict:
    """Insert a new user item."""
    item = {
        "PK": f"USER#{user_name}",
        "SK": user_id,
        "user_name": user_name,
        "user_id": user_id,
        "password": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _table().put_item(Item=item)
    return item

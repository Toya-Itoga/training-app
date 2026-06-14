"""Exercise table access layer (DynamoDB).

Schema (config/requirements.md):
  PK: EXERCISE#exercise_id (S)
  SK: user_name            (S)
  GSI: user_name-index (PK=SK=user_name) — for listing exercises by user
  Attributes: exercise_id, name, name_en, body_part
"""
import os
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from database import from_decimal, get_dynamodb


def _table():
    return get_dynamodb().Table(os.getenv("EXERCISE_TABLE_NAME", "exercises"))


def list_by_user(user_name: str) -> list[dict]:
    """Return all exercises for a user, ordered by exercise_id (ULID = time-ordered)."""
    resp = _table().query(
        IndexName="user_name-index",
        KeyConditionExpression=Key("SK").eq(user_name),
    )
    items = [from_decimal(i) for i in resp.get("Items", [])]
    return sorted(items, key=lambda e: e.get("exercise_id", ""))


def get(user_name: str, exercise_id: str) -> dict | None:
    """Return a single exercise or None."""
    resp = _table().get_item(Key={
        "PK": f"EXERCISE#{exercise_id}",
        "SK": user_name,
    })
    item = resp.get("Item")
    return from_decimal(item) if item else None


def create(user_name: str, exercise_id: str, data: dict) -> dict:
    """Insert a new exercise item."""
    item = {
        "PK": f"EXERCISE#{exercise_id}",
        "SK": user_name,
        "exercise_id": exercise_id,
        "name": data["name"],
        "name_en": data["name_en"].upper(),
        "body_part": data.get("body_part", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _table().put_item(Item=item)
    return from_decimal(item)


def update(user_name: str, exercise_id: str, data: dict) -> dict:
    """Update exercise attributes."""
    _table().update_item(
        Key={"PK": f"EXERCISE#{exercise_id}", "SK": user_name},
        UpdateExpression="SET #n = :name, name_en = :name_en, body_part = :body_part",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": data["name"],
            ":name_en": data["name_en"].upper(),
            ":body_part": data.get("body_part", ""),
        },
    )
    return get(user_name, exercise_id)


def delete(user_name: str, exercise_id: str) -> None:
    """Delete an exercise item."""
    _table().delete_item(Key={"PK": f"EXERCISE#{exercise_id}", "SK": user_name})

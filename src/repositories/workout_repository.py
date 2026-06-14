"""Workout table access layer (DynamoDB).

Schema (config/requirements.md):
  PK: USER#user_name         (S)
  SK: WORKOUT#YYYYMMDD#ULID  (S)
  Attributes: date (YYYY-MM-DD), exercises (list), updated_at

SK lexicographic ordering enables efficient date-range queries.
"""
import os
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key

from database import from_decimal, get_dynamodb, to_decimal
from ulid import ULID


def _table():
    return get_dynamodb().Table(os.getenv("WORKOUT_TABLE_NAME", "workouts"))


def _pk(user_name: str) -> str:
    return f"USER#{user_name}"


def _sk_prefix(date: str) -> str:
    """WORKOUT#YYYYMMDD from YYYY-MM-DD."""
    return f"WORKOUT#{date.replace('-', '')}"


def get(user_name: str, date: str) -> dict | None:
    """Return the workout for a specific date or None."""
    resp = _table().query(
        KeyConditionExpression=(
            Key("PK").eq(_pk(user_name)) &
            Key("SK").begins_with(_sk_prefix(date))
        )
    )
    items = resp.get("Items", [])
    return from_decimal(items[0]) if items else None


def list_in_range(user_name: str, date_from: str, date_to: str) -> list[dict]:
    """Return workouts with date between date_from and date_to (inclusive, YYYY-MM-DD)."""
    # Upper bound: append '~' (0x7E) after YYYYMMDD to capture all ULID suffixes for that day
    sk_from = _sk_prefix(date_from)
    sk_to   = f"{_sk_prefix(date_to)}~"
    resp = _table().query(
        KeyConditionExpression=(
            Key("PK").eq(_pk(user_name)) &
            Key("SK").between(sk_from, sk_to)
        )
    )
    return [from_decimal(i) for i in resp.get("Items", [])]


def list_recent(user_name: str, limit: int = 10) -> list[dict]:
    """Return the most recent workouts (up to limit), sorted newest first."""
    resp = _table().query(
        KeyConditionExpression=(
            Key("PK").eq(_pk(user_name)) &
            Key("SK").begins_with("WORKOUT#")
        ),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [from_decimal(i) for i in resp.get("Items", [])]


def save(user_name: str, date: str, exercises: list, sk: str | None = None) -> dict:
    """Upsert a workout. Reuses existing sk to update; generates new ULID for inserts."""
    sort_key = sk or f"{_sk_prefix(date)}#{str(ULID())}"
    item = {
        "PK": _pk(user_name),
        "SK": sort_key,
        "date": date,
        "exercises": to_decimal(exercises),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _table().put_item(Item=item)
    return from_decimal(item)


def delete(user_name: str, date: str) -> None:
    """Delete the workout for a given date (if it exists)."""
    existing = get(user_name, date)
    if existing:
        _table().delete_item(Key={"PK": _pk(user_name), "SK": existing["SK"]})

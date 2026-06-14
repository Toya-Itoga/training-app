"""DynamoDB connection setup.

ENV=development → DynamoDB Local (DYNAMODB_ENDPOINT)
ENV=production  → AWS DynamoDB
"""
import os
from decimal import Decimal

import boto3


def get_dynamodb():
    """Return a DynamoDB resource configured for the current environment."""
    env = os.getenv("ENV", "development")
    region = os.getenv("DYNAMODB_REGION", "ap-northeast-1")

    kwargs: dict = {
        "region_name": region,
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "dummy"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "dummy"),
    }

    if env == "development":
        endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:5434")
        kwargs["endpoint_url"] = endpoint

    return boto3.resource("dynamodb", **kwargs)


def get_table(table_env_key: str):
    """Get a DynamoDB Table object by its env-var key."""
    table_name = os.getenv(table_env_key, table_env_key.lower().replace("_table_name", "s"))
    return get_dynamodb().Table(table_name)


def to_decimal(obj: object) -> object:
    """Recursively convert float/int to Decimal for DynamoDB storage."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, int) and not isinstance(obj, bool):
        return Decimal(obj)
    if isinstance(obj, dict):
        return {k: to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_decimal(i) for i in obj]
    return obj


def from_decimal(obj: object) -> object:
    """Recursively convert Decimal to int/float when reading from DynamoDB."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: from_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [from_decimal(i) for i in obj]
    return obj


async def create_tables_if_not_exist() -> None:
    """Create DynamoDB tables if they don't exist (development only).

    Schema per config/requirements.md:
      User:     PK=USER#user_name / SK=user_id
      Exercise: PK=EXERCISE#exercise_id / SK=user_name  (GSI: user_name-index)
      Workout:  PK=USER#user_name / SK=WORKOUT#YYYYMMDD#ULID
    """
    dynamodb = get_dynamodb()

    definitions = [
        {
            "TableName": os.getenv("USER_TABLE_NAME", "users"),
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": os.getenv("EXERCISE_TABLE_NAME", "exercises"),
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "user_name-index",
                    "KeySchema": [{"AttributeName": "SK", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": os.getenv("WORKOUT_TABLE_NAME", "workouts"),
            "KeySchema": [
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
    ]

    existing = {t.name for t in dynamodb.tables.all()}
    for defn in definitions:
        if defn["TableName"] not in existing:
            try:
                dynamodb.create_table(**defn)
            except Exception as exc:
                print(f"[DB] table creation skipped: {exc}")

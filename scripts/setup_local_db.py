"""DynamoDB Local セットアップスクリプト.

テーブル作成とデフォルトデータ投入を行う。
スキーマは config/requirements.md に準拠。

Usage:
    python scripts/setup_local_db.py              # 既存テーブルはスキップ
    python scripts/setup_local_db.py --recreate   # 既存テーブルを削除して再作成
"""
import os
import sys
import time
from decimal import Decimal

# src/ を import パスに追加（既存モジュールを再利用）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import bcrypt
import boto3
from botocore.exceptions import ClientError
from ulid import ULID

# ── 接続設定 ─────────────────────────────────────────────────────────────────

ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:5434")
REGION   = os.getenv("DYNAMODB_REGION", "ap-northeast-1")
AWS_KEY  = os.getenv("AWS_ACCESS_KEY_ID", "dummy")
AWS_SEC  = os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")

USER_TABLE     = os.getenv("USER_TABLE_NAME",     "users")
EXERCISE_TABLE = os.getenv("EXERCISE_TABLE_NAME", "exercises")
WORKOUT_TABLE  = os.getenv("WORKOUT_TABLE_NAME",  "workouts")


def get_dynamodb():
    return boto3.resource(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SEC,
    )


# ── デフォルト種目データ ────────────────────────────────────────────────────

DEFAULT_EXERCISES = [
    # 胸
    {"name": "ベンチプレス",           "name_en": "BENCH PRESS",      "body_part": "chest"},
    {"name": "インクラインダンベル",     "name_en": "INCLINE DUMBBELL", "body_part": "chest"},
    {"name": "ダンベルフライ",          "name_en": "DUMBBELL FLY",     "body_part": "chest"},
    # 背中
    {"name": "デッドリフト",           "name_en": "DEADLIFT",         "body_part": "back"},
    {"name": "ラットプルダウン",         "name_en": "LAT PULLDOWN",     "body_part": "back"},
    {"name": "ベントオーバーロウ",       "name_en": "BENT-OVER ROW",    "body_part": "back"},
    # 脚
    {"name": "スクワット",             "name_en": "SQUAT",            "body_part": "legs"},
    {"name": "レッグプレス",           "name_en": "LEG PRESS",        "body_part": "legs"},
    {"name": "レッグカール",           "name_en": "LEG CURL",         "body_part": "legs"},
    # 肩
    {"name": "ショルダープレス",        "name_en": "SHOULDER PRESS",   "body_part": "shoulders"},
    {"name": "サイドレイズ",           "name_en": "SIDE RAISE",       "body_part": "shoulders"},
    # 腕
    {"name": "バーベルカール",          "name_en": "BARBELL CURL",     "body_part": "arms"},
    {"name": "トライセプスエクステンション", "name_en": "TRICEPS EXT.",  "body_part": "arms"},
]


# ── テーブル作成 ──────────────────────────────────────────────────────────────

def _table_exists(dynamodb, table_name: str) -> bool:
    try:
        dynamodb.Table(table_name).load()
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


def _delete_table(dynamodb, table_name: str) -> None:
    """テーブルを削除して ACTIVE になるまで待機する。"""
    try:
        dynamodb.Table(table_name).delete()
        print(f"[DEL]  {table_name} deleted, waiting...")
        # DynamoDB Local は即座に削除されることが多いが念のため少し待つ
        time.sleep(1)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise


def create_user_table(dynamodb, recreate: bool = False) -> None:
    """
    Userテーブル
      PK: USER#user_name (S)
      SK: user_id        (S)
    """
    if _table_exists(dynamodb, USER_TABLE):
        if not recreate:
            print(f"[SKIP] {USER_TABLE} already exists")
            return
        _delete_table(dynamodb, USER_TABLE)

    dynamodb.create_table(
        TableName=USER_TABLE,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"[OK]   {USER_TABLE} created  (PK=USER#user_name / SK=user_id)")


def create_exercise_table(dynamodb, recreate: bool = False) -> None:
    """
    Exerciseテーブル
      PK: EXERCISE#exercise_id (S)
      SK: user_name            (S)
      GSI: user_name-index (PK=user_name) — 種目一覧取得用
    """
    if _table_exists(dynamodb, EXERCISE_TABLE):
        if not recreate:
            print(f"[SKIP] {EXERCISE_TABLE} already exists")
            return
        _delete_table(dynamodb, EXERCISE_TABLE)

    dynamodb.create_table(
        TableName=EXERCISE_TABLE,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_name-index",
                "KeySchema": [{"AttributeName": "SK", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"[OK]   {EXERCISE_TABLE} created  (PK=EXERCISE#exercise_id / SK=user_name)")


def create_workout_table(dynamodb, recreate: bool = False) -> None:
    """
    Workoutテーブル
      PK: USER#user_name            (S)
      SK: WORKOUT#YYYYMMDD#ULID     (S)
    """
    if _table_exists(dynamodb, WORKOUT_TABLE):
        if not recreate:
            print(f"[SKIP] {WORKOUT_TABLE} already exists")
            return
        _delete_table(dynamodb, WORKOUT_TABLE)

    dynamodb.create_table(
        TableName=WORKOUT_TABLE,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"[OK]   {WORKOUT_TABLE} created  (PK=USER#user_name / SK=WORKOUT#YYYYMMDD#ULID)")


# ── データ投入 ────────────────────────────────────────────────────────────────

def seed_exercises(dynamodb, user_name: str = "default") -> None:
    """デフォルト種目を投入する。exercise_id は ULID で生成。"""
    table = dynamodb.Table(EXERCISE_TABLE)

    # 既に投入済みか確認（user_name-index を使用）
    existing = table.query(
        IndexName="user_name-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("SK").eq(user_name),
    )
    if existing.get("Count", 0) > 0:
        print(f"[SKIP] exercises for '{user_name}' already seeded ({existing['Count']} items)")
        return

    with table.batch_writer() as batch:
        for ex in DEFAULT_EXERCISES:
            exercise_id = str(ULID())
            batch.put_item(Item={
                "PK": f"EXERCISE#{exercise_id}",
                "SK": user_name,
                "exercise_id": exercise_id,
                "name":      ex["name"],
                "name_en":   ex["name_en"],
                "body_part": ex["body_part"],
            })

    print(f"[OK]   {len(DEFAULT_EXERCISES)} exercises seeded for user='{user_name}'")


def seed_test_user(dynamodb, user_name: str = "admin", password: str = "admin1234") -> None:
    """ローカル開発用テストユーザーを投入する。"""
    table = dynamodb.Table(USER_TABLE)

    # 既に存在するか確認
    existing = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(f"USER#{user_name}"),
    )
    if existing.get("Count", 0) > 0:
        print(f"[SKIP] user '{user_name}' already exists")
        return

    user_id = str(ULID())
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    table.put_item(Item={
        "PK":        f"USER#{user_name}",
        "SK":        user_id,
        "user_name": user_name,
        "user_id":   user_id,
        "email":     f"{user_name}@example.com",
        "password":  pw_hash,
    })
    print(f"[OK]   test user '{user_name}' created  (user_id={user_id})")


# ── エントリーポイント ────────────────────────────────────────────────────────

def main() -> None:
    recreate = "--recreate" in sys.argv
    print(f"Connecting to DynamoDB Local: {ENDPOINT}")
    if recreate:
        print("Mode: --recreate (既存テーブルを削除して再作成)\n")
    else:
        print("Mode: normal (既存テーブルはスキップ)\n")

    dynamodb = get_dynamodb()

    # テーブル作成
    create_user_table(dynamodb, recreate=recreate)
    create_exercise_table(dynamodb, recreate=recreate)
    create_workout_table(dynamodb, recreate=recreate)
    print()

    # データ投入
    seed_test_user(dynamodb)
    seed_exercises(dynamodb, user_name="admin")
    print("\nDone.")


if __name__ == "__main__":
    main()

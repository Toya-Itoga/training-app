"""Exercise business logic: CRUD + default seed data."""
from ulid import ULID

import repositories.exercise_repository as exercise_repo


# Default exercise catalogue (body_part per config/requirements.md)
_DEFAULT_EXERCISES = [
    {"name": "ベンチプレス",               "name_en": "BENCH PRESS",      "body_part": "chest"},
    {"name": "インクラインダンベル",         "name_en": "INCLINE DUMBBELL", "body_part": "chest"},
    {"name": "ダンベルフライ",              "name_en": "DUMBBELL FLY",     "body_part": "chest"},
    {"name": "デッドリフト",               "name_en": "DEADLIFT",         "body_part": "back"},
    {"name": "ラットプルダウン",             "name_en": "LAT PULLDOWN",     "body_part": "back"},
    {"name": "ベントオーバーロウ",           "name_en": "BENT-OVER ROW",    "body_part": "back"},
    {"name": "スクワット",                 "name_en": "SQUAT",            "body_part": "legs"},
    {"name": "レッグプレス",               "name_en": "LEG PRESS",        "body_part": "legs"},
    {"name": "レッグカール",               "name_en": "LEG CURL",         "body_part": "legs"},
    {"name": "ショルダープレス",            "name_en": "SHOULDER PRESS",   "body_part": "shoulders"},
    {"name": "サイドレイズ",               "name_en": "SIDE RAISE",       "body_part": "shoulders"},
    {"name": "バーベルカール",              "name_en": "BARBELL CURL",     "body_part": "arms"},
    {"name": "トライセプスエクステンション",  "name_en": "TRICEPS EXT.",     "body_part": "arms"},
]

# Part ordering for display
PARTS = [
    {"id": "chest",     "label": "胸",   "en": "CHEST",     "num": "01"},
    {"id": "back",      "label": "背中", "en": "BACK",      "num": "02"},
    {"id": "legs",      "label": "脚",   "en": "LEGS",      "num": "03"},
    {"id": "shoulders", "label": "肩",   "en": "SHOULDERS", "num": "04"},
    {"id": "arms",      "label": "腕",   "en": "ARMS",      "num": "05"},
]


def get_exercises(user_name: str) -> list[dict]:
    return exercise_repo.list_by_user(user_name)


def get_exercise(user_name: str, exercise_id: str) -> dict | None:
    return exercise_repo.get(user_name, exercise_id)


def create_exercise(user_name: str, data: dict) -> dict:
    exercise_id = str(ULID())
    return exercise_repo.create(user_name, exercise_id, data)


def update_exercise(user_name: str, exercise_id: str, data: dict) -> dict:
    return exercise_repo.update(user_name, exercise_id, data)


def delete_exercise(user_name: str, exercise_id: str) -> None:
    exercise_repo.delete(user_name, exercise_id)


def seed_default_exercises(user_name: str) -> None:
    """Insert the default exercises for a newly registered user."""
    for ex in _DEFAULT_EXERCISES:
        exercise_repo.create(user_name, str(ULID()), ex)


def group_by_part(exercises: list[dict]) -> list[dict]:
    """Return exercises grouped by body_part in the canonical PARTS order."""
    grouped = []
    for part in PARTS:
        items = [e for e in exercises if e.get("body_part") == part["id"]]
        grouped.append({**part, "exercises": items})
    return grouped

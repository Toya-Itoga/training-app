"""Workout business logic: save, query, and aggregate workout data."""
from datetime import datetime, timedelta, timezone

import repositories.workout_repository as workout_repo
import repositories.exercise_repository as exercise_repo


def get_workout(user_name: str, date: str) -> dict | None:
    return workout_repo.get(user_name, date)


def save_workout(user_name: str, date: str, exercises: list[dict]) -> dict:
    """Upsert today's workout. exercises is a list of {exercise_id, sets}."""
    existing = workout_repo.get(user_name, date)
    # Reuse the existing SK to overwrite; None triggers new ULID in the repo
    existing_sk = existing.get("SK") if existing else None
    return workout_repo.save(user_name, date, exercises, sk=existing_sk)


def get_recent_workouts(user_name: str, limit: int = 3) -> list[dict]:
    """Return the N most recent workouts with exercise details resolved."""
    workouts = workout_repo.list_recent(user_name, limit)
    return [_resolve_exercises(user_name, w) for w in workouts]


def get_workouts_in_month(user_name: str, year: int, month: int) -> dict[str, dict]:
    """Return {date: workout} map for all workouts in the given month."""
    date_from = f"{year}-{month:02d}-01"
    # End of month: last day
    if month == 12:
        date_to = f"{year + 1}-01-01"
    else:
        date_to = f"{year}-{month + 1:02d}-01"
    end = (datetime.strptime(date_to, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    workouts = workout_repo.list_in_range(user_name, date_from, end)
    return {w["date"]: _resolve_exercises(user_name, w) for w in workouts}


def get_week_stats(user_name: str) -> dict:
    """Compute stats for the current ISO week (Mon–Sun)."""
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    workouts_map = {
        w["date"]: w
        for w in workout_repo.list_in_range(
            user_name, monday.isoformat(), sunday.isoformat()
        )
    }

    day_volumes: list[int] = []
    for i in range(7):
        d = (monday + timedelta(days=i)).isoformat()
        w = workouts_map.get(d)
        vol = _calc_volume(w["exercises"]) if w else 0
        day_volumes.append(vol)

    week_count = sum(1 for v in day_volumes if v > 0)
    total_vol = sum(day_volumes)

    return {
        "today": today.isoformat(),
        "monday": monday.isoformat(),
        "day_volumes": day_volumes,
        "week_count": week_count,
        "total_volume": total_vol,
        "avg_volume": total_vol // week_count if week_count else 0,
        "max_volume": max(day_volumes) if day_volumes else 0,
    }


# ── helpers ──────────────────────────────────────────────────────────────────

def _calc_volume(exercises: list[dict]) -> int:
    """Sum reps × weight across all sets in all exercises."""
    total = 0
    for ex in exercises:
        for s in ex.get("sets", []):
            total += s.get("reps", 0) * s.get("weight", 0)
    return int(total)


def _resolve_exercises(user_name: str, workout: dict) -> dict:
    """Attach exercise metadata (name, body_part) to each exercise block."""
    resolved = []
    for block in workout.get("exercises", []):
        ex = exercise_repo.get(user_name, block["exercise_id"])
        resolved.append({**block, "exercise": ex or {}})
    return {
        **workout,
        "exercises": resolved,
        "total_volume": _calc_volume(workout.get("exercises", [])),
    }

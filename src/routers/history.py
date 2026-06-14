"""History routes: calendar view + HTMX partials.

GET /history                       → full history page (current month)
GET /history/calendar/{year}/{month} → calendar partial (HTMX swap)
GET /history/day/{date}            → day detail partial (HTMX swap)
"""
from datetime import datetime, timezone, timedelta
from calendar import monthrange

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import services.workout_service as workout_svc
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

_MONTH_NAMES = [
    "JANUARY","FEBRUARY","MARCH","APRIL","MAY","JUNE",
    "JULY","AUGUST","SEPTEMBER","OCTOBER","NOVEMBER","DECEMBER",
]
_MONTH_SHORT = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date()
    return await _render_history(request, user, today.year, today.month, selected=None)


@router.get("/history/calendar/{year}/{month}", response_class=HTMLResponse)
async def calendar_partial(
    request: Request,
    year: int,
    month: int,
    selected: str | None = None,
    user: dict = Depends(get_current_user),
):
    """Return only the calendar + day-detail panel (HTMX swap)."""
    ctx = await _build_calendar_ctx(user["username"], year, month, selected)
    return templates.TemplateResponse(request, "partials/calendar.html", ctx)


@router.get("/history/day/{date}", response_class=HTMLResponse)
async def day_detail(
    request: Request,
    date: str,
    user: dict = Depends(get_current_user),
):
    """Return the day-detail panel only (HTMX swap for day selection)."""
    workout = workout_svc.get_workout(user["username"], date)
    ctx = _build_day_ctx(date, workout)
    return templates.TemplateResponse(request, "partials/day_detail.html", ctx)


# ── helpers ──────────────────────────────────────────────────────────────────

async def _render_history(
    request: Request, user: dict, year: int, month: int, selected: str | None
) -> HTMLResponse:
    ctx = await _build_calendar_ctx(user["username"], year, month, selected)
    day_ctx = {}
    if selected and ctx["workouts_map"].get(selected):
        day_ctx = _build_day_ctx(selected, ctx["workouts_map"][selected])
    return templates.TemplateResponse(request, "history.html", {
        "user": user,
        **ctx,
        **day_ctx,
    })


async def _build_calendar_ctx(user_id: str, year: int, month: int, selected: str | None) -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    workouts_map = workout_svc.get_workouts_in_month(user_id, year, month)

    # Build calendar grid (Monday-first)
    first_dow = (datetime(year, month, 1).weekday())  # 0=Mon
    days_in_month = monthrange(year, month)[1]

    cells = [None] * first_dow
    for d in range(1, days_in_month + 1):
        cells.append(d)
    while len(cells) % 7 != 0:
        cells.append(None)

    def iso(d):
        return f"{year}-{month:02d}-{d:02d}"

    calendar_rows = []
    for week_start in range(0, len(cells), 7):
        row = []
        for d in cells[week_start:week_start + 7]:
            if d is None:
                row.append({"empty": True})
            else:
                date_iso = iso(d)
                workout = workouts_map.get(date_iso)
                part_tags = []
                if workout:
                    seen = set()
                    for ex_block in workout.get("exercises", []):
                        part = ex_block.get("exercise", {}).get("body_part", "")
                        if part and part not in seen:
                            seen.add(part)
                            part_tags.append(part[:3].upper())
                row.append({
                    "empty": False,
                    "day": d,
                    "iso": date_iso,
                    "is_today": date_iso == today,
                    "is_selected": date_iso == selected,
                    "has_workout": bool(workout),
                    "part_tags": part_tags[:3],
                })
        calendar_rows.append(row)

    return {
        "year": year,
        "month": month,
        "month_name": _MONTH_NAMES[month - 1],
        "today": today,
        "selected": selected,
        "calendar_rows": calendar_rows,
        "workouts_map": workouts_map,
    }


def _build_day_ctx(date: str, workout: dict | None) -> dict:
    if not workout:
        return {"selected_date": date, "day_workout": None}

    d = datetime.strptime(date, "%Y-%m-%d")
    exercises = workout.get("exercises", [])
    total_vol = sum(
        sum(s.get("reps", 0) * s.get("weight", 0) for s in ex.get("sets", []))
        for ex in exercises
    )
    total_sets = sum(len(ex.get("sets", [])) for ex in exercises)

    return {
        "selected_date": date,
        "selected_display": f"{d.day} {_MONTH_SHORT[d.month - 1]}",
        "selected_weekday": ["SUN","MON","TUE","WED","THU","FRI","SAT"][d.weekday()],
        "day_workout": {
            "exercises": exercises,
            "total_volume": int(total_vol),
            "total_sets": total_sets,
            "exercise_count": len(exercises),
        },
    }

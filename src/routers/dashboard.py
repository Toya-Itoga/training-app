"""Dashboard route: home screen with weekly stats."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import services.workout_service as workout_svc
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

_DAY_LABELS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
_MONTH_SHORT = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    stats = workout_svc.get_week_stats(user["username"])
    recent = workout_svc.get_recent_workouts(user["username"], limit=3)

    day_volumes = stats["day_volumes"]
    max_vol = max(day_volumes) if any(day_volumes) else 1

    # Build chart columns for the week
    chart_cols = []
    for i, vol in enumerate(day_volumes):
        chart_cols.append({
            "label": _DAY_LABELS[i],
            "volume": vol,
            "height_pct": max(8, int(vol / max_vol * 100)) if vol > 0 else 0,
            "done": vol > 0,
            "is_today": (stats["monday"] and i == _weekday_index(stats["today"])),
        })

    # Enrich recent workouts for display
    recent_display = []
    for w in recent:
        from datetime import datetime
        d = datetime.strptime(w["date"], "%Y-%m-%d")
        exs = w.get("exercises", [])
        first_ex = exs[0].get("exercise", {}) if exs else {}
        total_sets = sum(len(ex.get("sets", [])) for ex in exs)
        recent_display.append({
            "date": w["date"],
            "day": d.day,
            "month": _MONTH_SHORT[d.month - 1],
            "part_label": _part_label(first_ex.get("body_part", "")),
            "exercise_names": " · ".join(ex.get("exercise", {}).get("name", "") for ex in exs[:4]),
            "total_sets": total_sets,
            "total_volume": w.get("total_volume", 0),
        })

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "stats": stats,
        "chart_cols": chart_cols,
        "recent": recent_display,
    })


def _weekday_index(iso_date: str) -> int:
    from datetime import datetime
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return d.weekday()  # 0=Mon


def _part_label(part: str) -> str:
    labels = {
        "chest": "CHEST", "back": "BACK", "legs": "LEGS",
        "shoulders": "SHOULDERS", "arms": "ARMS",
    }
    return labels.get(part, "—")

"""Training record routes.

GET  /record           → recording screen (optional ?date=YYYY-MM-DD)
POST /record/save      → save workout (JSON body from Alpine.js)
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import services.exercise_service as exercise_svc
import services.workout_service as workout_svc
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/record", response_class=HTMLResponse)
async def record_page(
    request: Request,
    date: str | None = None,
    user: dict = Depends(get_current_user),
):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    selected_date = date or today

    # Load existing workout for this date (for edit flow from history)
    existing = workout_svc.get_workout(user["username"], selected_date)

    exercises = exercise_svc.get_exercises(user["username"])
    parts = exercise_svc.PARTS

    # Prepare existing blocks for Alpine.js initialisation
    initial_blocks = []
    if existing:
        for block in existing.get("exercises", []):
            ex = exercise_svc.get_exercise(user["username"], block["exercise_id"])
            if ex:
                initial_blocks.append({
                    "exercise_id": block["exercise_id"],
                    "exercise": ex,
                    "sets": block.get("sets", []),
                })

    return templates.TemplateResponse(request, "record.html", {
        "user": user,
        "selected_date": selected_date,
        "today": today,
        "exercises_json": json.dumps(exercises, ensure_ascii=False),
        "parts": parts,
        "initial_blocks_json": json.dumps(initial_blocks, ensure_ascii=False),
    })


@router.post("/record/save")
async def save_record(request: Request, user: dict = Depends(get_current_user)):
    """Save a workout session. Body: { date, blocks: [{exercise_id, sets}] }"""
    body = await request.json()
    date = body.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    blocks = body.get("blocks", [])

    # Normalise sets (convert reps/weight to numbers)
    exercises_to_save = [
        {
            "exercise_id": b["exercise_id"],
            "sets": [
                {"reps": int(s.get("reps", 0)), "weight": float(s.get("weight", 0))}
                for s in b.get("sets", [])
            ],
        }
        for b in blocks
    ]

    workout_svc.save_workout(user["username"], date, exercises_to_save)
    return JSONResponse({"ok": True})

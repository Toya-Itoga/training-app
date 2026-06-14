"""Exercise management routes.

GET    /exercises              → exercise list page
POST   /exercises              → create new exercise (form submit)
POST   /exercises/{id}/update → update exercise (form submit, no PUT for HTML forms)
POST   /exercises/{id}/delete → delete exercise (form submit)
"""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import services.exercise_service as exercise_svc
from utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/exercises", response_class=HTMLResponse)
async def exercises_page(request: Request, user: dict = Depends(get_current_user)):
    exercises = exercise_svc.get_exercises(user["username"])
    grouped = exercise_svc.group_by_part(exercises)
    return templates.TemplateResponse(request, "exercises.html", {
        "user": user,
        "grouped": grouped,
        "parts": exercise_svc.PARTS,
        "total": len(exercises),
    })


@router.post("/exercises", response_class=RedirectResponse)
async def create_exercise(
    request: Request,
    name: str = Form(...),
    name_en: str = Form(...),
    body_part: str = Form(...),
    user: dict = Depends(get_current_user),
):
    exercise_svc.create_exercise(user["username"], {
        "name": name,
        "name_en": name_en,
        "body_part": body_part,
    })
    return RedirectResponse(url="/exercises", status_code=303)


@router.post("/exercises/{exercise_id}/update", response_class=RedirectResponse)
async def update_exercise(
    exercise_id: str,
    name: str = Form(...),
    name_en: str = Form(...),
    body_part: str = Form(...),
    user: dict = Depends(get_current_user),
):
    exercise_svc.update_exercise(user["username"], exercise_id, {
        "name": name,
        "name_en": name_en,
        "body_part": body_part,
    })
    return RedirectResponse(url="/exercises", status_code=303)


@router.post("/exercises/{exercise_id}/delete", response_class=RedirectResponse)
async def delete_exercise(
    exercise_id: str,
    user: dict = Depends(get_current_user),
):
    exercise_svc.delete_exercise(user["username"], exercise_id)
    return RedirectResponse(url="/exercises", status_code=303)

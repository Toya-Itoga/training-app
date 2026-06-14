"""Authentication routes: login / logout."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import services.auth_service as auth_svc

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Already logged in → redirect to dashboard
    if request.cookies.get("access_token"):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html")


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    token = auth_svc.login(username, password)
    if token is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "認証に失敗しました。資格情報を確認してください。"},
            status_code=401,
        )
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=6 * 3600,
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

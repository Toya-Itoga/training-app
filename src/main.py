"""IRONLOG — 筋トレ記録アプリ エントリーポイント.

Run locally (project root):
    python -m uvicorn src.main:app --reload

Lambda handler: `main.handler`
"""
import os
import sys

# Ensure src/ is in sys.path and is the working directory so that
# "static" / "templates" relative paths and bare imports resolve correctly
# both in local development (cwd = project root) and on Lambda (cwd = src/).
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
os.chdir(_SRC_DIR)

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from routers import auth, dashboard, record, history, exercises
from database import create_tables_if_not_exist

app = FastAPI(title="IRONLOG", docs_url=None, redoc_url=None)

# Static files and templates are relative to src/ (CLAUDE.md Lambda rule)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(record.router)
app.include_router(history.router)
app.include_router(exercises.router)


@app.on_event("startup")
async def startup():
    """Create DynamoDB tables if they don't exist (development)."""
    if os.getenv("ENV", "development") == "development":
        await create_tables_if_not_exist()


@app.exception_handler(401)
async def auth_error_handler(request: Request, exc):
    return RedirectResponse(url="/login", status_code=302)


# AWS Lambda handler
handler = Mangum(app)

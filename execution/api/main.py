"""
main.py — FastAPI application entry point.

Run with:
    uvicorn execution.api.main:app --reload --port 8000
"""

from pathlib import Path
import os
import json
from fastapi.responses import Response

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from execution.api.routers import recipes, shopping_list, tags, users, households, meal_plan, passkeys


app = FastAPI(
    title="Onionary — Recipe API",
    version=os.getenv("APP_VERSION", "0.2.0-dev"),
    description="Manage recipes, plan weekly meals, and generate shopping lists.",
)

# Credentialed browser requests are restricted to the configured public origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[passkeys.origin()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(passkeys.router)
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(shopping_list.router)
app.include_router(users.router)
app.include_router(households.router)
app.include_router(meal_plan.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


from execution.admin import configure_admin
configure_admin(app)

@app.get("/translations.js", include_in_schema=False)
def translations():
    directory = Path(__file__).resolve().parents[2] / "frontend/locales"
    dictionaries = {lang: json.loads((directory / f"{lang}.json").read_text()) for lang in ("en", "de")}
    return Response("window.OnionaryTranslations=" + json.dumps(dictionaries, ensure_ascii=True) + ";", media_type="application/javascript", headers={"Cache-Control": "no-cache"})


# Serve frontend static files (must be last — catches all unmatched routes)
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

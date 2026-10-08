"""
main.py — FastAPI application entry point.

Run with:
    uvicorn execution.api.main:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from execution.api.routers import recipes, shopping_list, tags, users, households, meal_plan, passkeys


app = FastAPI(
    title="What Should We Eat — Recipe API",
    version="0.1.0",
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


# Serve frontend static files (must be last — catches all unmatched routes)
_frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

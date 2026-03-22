"""
main.py — FastAPI application entry point.

Run with:
    uvicorn execution.api.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from execution.api.routers import recipes, shopping_list, tags

app = FastAPI(
    title="What Should We Eat — Recipe API",
    version="0.1.0",
    description="Manage recipes, plan weekly meals, and generate shopping lists.",
)

# CORS — allow everything during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(recipes.router)
app.include_router(tags.router)
app.include_router(shopping_list.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

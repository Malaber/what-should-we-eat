"""
test_api.py — Smoke tests for the Recipe API.

Usage:
    # Start the stack first, then:
    python -m execution.tests.test_api
"""

import sys

import httpx

BASE = "http://localhost:8000"


def check(label: str, passed: bool, detail: str = ""):
    status = "✅" if passed else "❌"
    print(f"  {status} {label}" + (f" — {detail}" if detail else ""))
    if not passed:
        raise AssertionError(f"FAILED: {label} {detail}")


def main():
    c = httpx.Client(base_url=BASE, timeout=10)

    # ── Health ───────────────────────────────────────────────────────
    print("\n🏥 Health check")
    r = c.get("/health")
    check("GET /health", r.status_code == 200, r.text)

    # ── Create recipe ────────────────────────────────────────────────
    print("\n📝 Create recipe")
    recipe_data = {
        "name": "Chicken Stir-Fry",
        "kcal_per_serving": 450,
        "active_cooking_time_min": 15,
        "total_time_min": 25,
        "ingredients": [
            {"name": "chicken breast", "quantity": 300, "unit": "g"},
            {"name": "soy sauce", "quantity": 2, "unit": "tbsp"},
            {"name": "bell pepper", "quantity": 1, "unit": "piece"},
        ],
        "instruction_steps": [
            {"step_number": 1, "description": "Slice chicken into strips", "duration_min": 5},
            {"step_number": 2, "description": "Stir-fry chicken on high heat", "duration_min": 7},
            {"step_number": 3, "description": "Add vegetables, cook until tender", "duration_min": 5},
        ],
        "tags": ["high protein", "quick"],
    }
    r = c.post("/recipes", json=recipe_data)
    check("POST /recipes → 201", r.status_code == 201, f"id={r.json().get('id')}")
    recipe_id = r.json()["id"]

    # Create a second recipe for filter / random / shopping tests
    recipe2_data = {
        "name": "Pasta Pomodoro",
        "kcal_per_serving": 520,
        "active_cooking_time_min": 10,
        "total_time_min": 20,
        "ingredients": [
            {"name": "pasta", "quantity": 250, "unit": "g"},
            {"name": "canned tomatoes", "quantity": 400, "unit": "g"},
            {"name": "bell pepper", "quantity": 2, "unit": "piece"},
        ],
        "instruction_steps": [
            {"step_number": 1, "description": "Boil pasta", "duration_min": 10},
            {"step_number": 2, "description": "Simmer tomato sauce", "duration_min": 8},
        ],
        "tags": ["vegetarian", "quick"],
    }
    r = c.post("/recipes", json=recipe2_data)
    check("POST /recipes (second) → 201", r.status_code == 201)
    recipe2_id = r.json()["id"]

    # ── Read ─────────────────────────────────────────────────────────
    print("\n📖 Read recipes")
    r = c.get("/recipes")
    check("GET /recipes → 200", r.status_code == 200, f"count={len(r.json())}")
    check("Contains both recipes", len(r.json()) >= 2)

    r = c.get(f"/recipes/{recipe_id}")
    check("GET /recipes/{id} → 200", r.status_code == 200, f"name={r.json()['name']}")
    check("Has 3 ingredients", len(r.json()["ingredients"]) == 3)
    check("Has 3 instruction steps", len(r.json()["instruction_steps"]) == 3)
    check("Has 2 tags", len(r.json()["tags"]) == 2)

    # ── Filter by tag ────────────────────────────────────────────────
    print("\n🔍 Filter")
    r = c.get("/recipes", params={"tag": "high protein"})
    check("Filter tag='high protein'", len(r.json()) == 1 and r.json()[0]["name"] == "Chicken Stir-Fry")

    r = c.get("/recipes", params={"tag": "quick"})
    check("Filter tag='quick' → 2 results", len(r.json()) == 2)

    r = c.get("/recipes", params={"max_kcal": 500})
    check("Filter max_kcal=500 → 1 result", len(r.json()) == 1)

    # ── Random ───────────────────────────────────────────────────────
    print("\n🎲 Random selection")
    r = c.post("/recipes/random", json={"count": 1, "tag_names": ["quick"]})
    check("Random 1 from 'quick' → 200", r.status_code == 200 and len(r.json()) == 1)

    # ── Shopping list ────────────────────────────────────────────────
    print("\n🛒 Shopping list")
    r = c.post("/shopping-list", json=[recipe_id, recipe2_id])
    check("POST /shopping-list → 200", r.status_code == 200)
    items = r.json()["items"]
    # bell pepper should be merged: 1 + 2 = 3 pieces
    bell = next((i for i in items if i["name"] == "bell pepper"), None)
    check("Bell pepper merged → 3 pieces", bell is not None and bell["total_quantity"] == 3.0)

    # ── Update ───────────────────────────────────────────────────────
    print("\n✏️  Update recipe")
    r = c.put(f"/recipes/{recipe_id}", json={"name": "Spicy Chicken Stir-Fry"})
    check("PUT /recipes/{id} → 200", r.status_code == 200)
    check("Name updated", r.json()["name"] == "Spicy Chicken Stir-Fry")

    # ── Delete ───────────────────────────────────────────────────────
    print("\n🗑️  Delete recipe")
    r = c.delete(f"/recipes/{recipe_id}")
    check("DELETE /recipes/{id} → 204", r.status_code == 204)
    r = c.get(f"/recipes/{recipe_id}")
    check("GET deleted → 404", r.status_code == 404)

    # ── Tags ─────────────────────────────────────────────────────────
    print("\n🏷️  Tags")
    r = c.get("/tags")
    check("GET /tags → 200", r.status_code == 200)
    tag_names = [t["name"] for t in r.json()]
    check("Tags include 'high protein'", "high protein" in tag_names)

    # Clean up second recipe
    c.delete(f"/recipes/{recipe2_id}")

    print("\n✅ All smoke tests passed!\n")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\n💥 {e}")
        sys.exit(1)

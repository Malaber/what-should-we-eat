"""
test_recipes.py — CRUD, filter, and random-selection tests for recipes.
"""

from execution.tests.helpers import make_recipe_payload


class TestRecipeCreate:
    def test_create_recipe(self, client, auth_headers):
        r = client.post("/recipes", json=make_recipe_payload(), headers=auth_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Test Recipe"
        assert len(body["ingredients"]) == 2
        assert len(body["instruction_steps"]) == 2
        assert len(body["tags"]) == 2

    def test_create_recipe_unauthenticated(self, client):
        r = client.post("/recipes", json=make_recipe_payload())
        assert r.status_code == 401

    def test_create_minimal_recipe(self, client, auth_headers):
        r = client.post("/recipes", json={"name": "Minimal"}, headers=auth_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Minimal"
        assert body["ingredients"] == []
        assert body["instruction_steps"] == []
        assert body["tags"] == []


class TestRecipeRead:
    def test_list_recipes(self, client, auth_headers):
        client.post("/recipes", json=make_recipe_payload("A"), headers=auth_headers)
        client.post("/recipes", json=make_recipe_payload("B"), headers=auth_headers)
        r = client.get("/recipes", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_recipe_by_id(self, client, auth_headers):
        created = client.post("/recipes", json=make_recipe_payload(), headers=auth_headers).json()
        r = client.get(f"/recipes/{created['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Test Recipe"

    def test_get_nonexistent_recipe_returns_404(self, client, auth_headers):
        r = client.get("/recipes/9999", headers=auth_headers)
        assert r.status_code == 404


class TestRecipeFilter:
    def test_filter_by_tag(self, client, auth_headers):
        client.post("/recipes", json=make_recipe_payload("Chicken", tags=["protein"]), headers=auth_headers)
        client.post("/recipes", json=make_recipe_payload("Salad", tags=["veggie"]), headers=auth_headers)

        r = client.get("/recipes", params={"tag": "protein"}, headers=auth_headers)
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Chicken"

    def test_filter_by_max_kcal(self, client, auth_headers):
        client.post("/recipes", json=make_recipe_payload("Low", kcal=200), headers=auth_headers)
        client.post("/recipes", json=make_recipe_payload("High", kcal=800), headers=auth_headers)

        r = client.get("/recipes", params={"max_kcal": 500}, headers=auth_headers)
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Low"

    def test_filter_by_max_total_time(self, client, auth_headers):
        payload_fast = make_recipe_payload("Fast")
        payload_fast["total_time_min"] = 15
        payload_slow = make_recipe_payload("Slow")
        payload_slow["total_time_min"] = 120

        client.post("/recipes", json=payload_fast, headers=auth_headers)
        client.post("/recipes", json=payload_slow, headers=auth_headers)

        r = client.get("/recipes", params={"max_total_time": 30}, headers=auth_headers)
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Fast"


class TestRecipeUpdate:
    def test_update_name(self, client, auth_headers):
        created = client.post("/recipes", json=make_recipe_payload(), headers=auth_headers).json()
        r = client.put(f"/recipes/{created['id']}", json={"name": "Updated"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Updated"
        # Other fields preserved
        assert r.json()["kcal_per_serving"] == 400

    def test_update_ingredients_replaces(self, client, auth_headers):
        created = client.post("/recipes", json=make_recipe_payload(), headers=auth_headers).json()
        r = client.put(f"/recipes/{created['id']}", json={
            "ingredients": [{"name": "tofu", "quantity": 150, "unit": "g"}],
        }, headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["ingredients"]) == 1
        assert r.json()["ingredients"][0]["name"] == "tofu"

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        r = client.put("/recipes/9999", json={"name": "Nope"}, headers=auth_headers)
        assert r.status_code == 404


class TestRecipeDelete:
    def test_delete_recipe(self, client, auth_headers):
        created = client.post("/recipes", json=make_recipe_payload(), headers=auth_headers).json()
        r = client.delete(f"/recipes/{created['id']}", headers=auth_headers)
        assert r.status_code == 204

        r = client.get(f"/recipes/{created['id']}", headers=auth_headers)
        assert r.status_code == 404

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        r = client.delete("/recipes/9999", headers=auth_headers)
        assert r.status_code == 404


class TestRecipeRandom:
    def test_random_selection(self, client, auth_headers):
        for i in range(5):
            client.post("/recipes", json=make_recipe_payload(f"R{i}"), headers=auth_headers)

        r = client.post("/recipes/random", json={"count": 2}, headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_random_fewer_than_count(self, client, auth_headers):
        client.post("/recipes", json=make_recipe_payload(), headers=auth_headers)
        r = client.post("/recipes/random", json={"count": 10}, headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_random_with_exclude(self, client, auth_headers):
        ids = []
        for i in range(3):
            created = client.post("/recipes", json=make_recipe_payload(f"R{i}"), headers=auth_headers).json()
            ids.append(created["id"])

        r = client.post("/recipes/random", json={
            "count": 10, "exclude_ids": ids[:2],
        }, headers=auth_headers)
        assert r.status_code == 200
        result_ids = {item["id"] for item in r.json()}
        assert ids[0] not in result_ids
        assert ids[1] not in result_ids


class TestRecipeHouseholdIsolation:
    def test_recipes_scoped_to_household(self, client, auth_headers, second_user_headers):
        """Alice and Bob each have their own household — they shouldn't see each other's recipes."""
        client.post("/recipes", json=make_recipe_payload("Alice's Dish"), headers=auth_headers)
        client.post("/recipes", json=make_recipe_payload("Bob's Dish"), headers=second_user_headers)

        alice_recipes = client.get("/recipes", headers=auth_headers).json()
        bob_recipes = client.get("/recipes", headers=second_user_headers).json()

        assert len(alice_recipes) == 1
        assert alice_recipes[0]["name"] == "Alice's Dish"
        assert len(bob_recipes) == 1
        assert bob_recipes[0]["name"] == "Bob's Dish"

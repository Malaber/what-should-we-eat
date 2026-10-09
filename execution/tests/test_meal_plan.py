"""
test_meal_plan.py — Meal plan CRUD and cooked-status tests.
"""

from execution.tests.helpers import make_recipe_payload


def _create_recipe(client, headers, name="Meal"):
    r = client.post("/recipes", json=make_recipe_payload(name), headers=headers)
    return r.json()["id"]


class TestMealPlanGet:
    def test_empty_meal_plan(self, client, auth_headers):
        r = client.get("/meal-plan", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["items"] == []


class TestMealPlanAdd:
    def test_add_to_meal_plan(self, client, auth_headers):
        rid = _create_recipe(client, auth_headers)
        r = client.post("/meal-plan/add", json={"recipe_ids": [rid]}, headers=auth_headers)
        assert r.status_code == 201
        assert len(r.json()["items"]) == 1
        assert r.json()["items"][0]["recipe_id"] == rid
        assert r.json()["items"][0]["is_cooked"] is False

    def test_add_duplicate_is_idempotent(self, client, auth_headers):
        rid = _create_recipe(client, auth_headers)
        client.post("/meal-plan/add", json={"recipe_ids": [rid]}, headers=auth_headers)
        r = client.post("/meal-plan/add", json={"recipe_ids": [rid]}, headers=auth_headers)
        assert len(r.json()["items"]) == 1


class TestMealPlanReplace:
    def test_replace_meal_plan(self, client, auth_headers):
        r1 = _create_recipe(client, auth_headers, "A")
        r2 = _create_recipe(client, auth_headers, "B")
        r3 = _create_recipe(client, auth_headers, "C")

        # Add r1 and r2
        client.post("/meal-plan/add", json={"recipe_ids": [r1, r2]}, headers=auth_headers)

        # Replace with r3 only
        r = client.put("/meal-plan", json={"recipe_ids": [r3]}, headers=auth_headers)
        assert r.status_code == 200
        ids = {item["recipe_id"] for item in r.json()["items"]}
        assert ids == {r3}


class TestMealPlanCooked:
    def test_mark_cooked(self, client, auth_headers):
        rid = _create_recipe(client, auth_headers)
        client.post("/meal-plan/add", json={"recipe_ids": [rid]}, headers=auth_headers)

        r = client.post(f"/meal-plan/{rid}/cooked", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["is_cooked"] is True

    def test_unmark_cooked(self, client, auth_headers):
        rid = _create_recipe(client, auth_headers)
        client.post("/meal-plan/add", json={"recipe_ids": [rid]}, headers=auth_headers)
        client.post(f"/meal-plan/{rid}/cooked", headers=auth_headers)

        r = client.delete(f"/meal-plan/{rid}/cooked", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["is_cooked"] is False

    def test_mark_cooked_not_in_plan_returns_404(self, client, auth_headers):
        r = client.post("/meal-plan/9999/cooked", headers=auth_headers)
        assert r.status_code == 404


class TestMealPlanRemove:
    def test_remove_single(self, client, auth_headers):
        rid = _create_recipe(client, auth_headers)
        client.post("/meal-plan/add", json={"recipe_ids": [rid]}, headers=auth_headers)

        r = client.delete(f"/meal-plan/{rid}", headers=auth_headers)
        assert r.status_code == 204

        plan = client.get("/meal-plan", headers=auth_headers).json()
        assert plan["items"] == []

    def test_remove_not_in_plan_returns_404(self, client, auth_headers):
        r = client.delete("/meal-plan/9999", headers=auth_headers)
        assert r.status_code == 404

    def test_clear_meal_plan(self, client, auth_headers):
        r1 = _create_recipe(client, auth_headers, "A")
        r2 = _create_recipe(client, auth_headers, "B")
        client.post("/meal-plan/add", json={"recipe_ids": [r1, r2]}, headers=auth_headers)

        r = client.delete("/meal-plan", headers=auth_headers)
        assert r.status_code == 204

        plan = client.get("/meal-plan", headers=auth_headers).json()
        assert plan["items"] == []


class TestMealPlanHouseholdIsolation:
    def test_meal_plan_scoped_to_household(self, client, auth_headers, second_user_headers):
        rid_alice = _create_recipe(client, auth_headers, "Alice Meal")
        rid_bob = _create_recipe(client, second_user_headers, "Bob Meal")

        client.post("/meal-plan/add", json={"recipe_ids": [rid_alice]}, headers=auth_headers)
        client.post("/meal-plan/add", json={"recipe_ids": [rid_bob]}, headers=second_user_headers)

        alice_plan = client.get("/meal-plan", headers=auth_headers).json()
        bob_plan = client.get("/meal-plan", headers=second_user_headers).json()

        assert len(alice_plan["items"]) == 1
        assert alice_plan["items"][0]["recipe"]["name"] == "Alice Meal"
        assert len(bob_plan["items"]) == 1
        assert bob_plan["items"][0]["recipe"]["name"] == "Bob Meal"


def test_foreign_recipe_rejected_before_replacing_plan(client, auth_headers, second_user_headers):
    own = _create_recipe(client, auth_headers, "Own")
    foreign = _create_recipe(client, second_user_headers, "Private")
    client.post('/meal-plan/add', json={'recipe_ids': [own, own]}, headers=auth_headers)
    for method, path in [('post', '/meal-plan/add'), ('put', '/meal-plan')]:
        assert getattr(client, method)(path, json={'recipe_ids': [foreign]}, headers=auth_headers).status_code == 404
    assert [i['recipe_id'] for i in client.get('/meal-plan', headers=auth_headers).json()['items']] == [own]
    assert client.post('/shopping-list', json=[foreign], headers=auth_headers).status_code == 404

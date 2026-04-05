"""
test_shopping_list.py — Shopping list aggregation tests.
"""

from execution.tests.helpers import make_recipe_payload


class TestShoppingList:
    def test_generate_shopping_list(self, client, auth_headers):
        r1 = client.post("/recipes", json=make_recipe_payload("A"), headers=auth_headers).json()
        r2 = client.post("/recipes", json=make_recipe_payload("B"), headers=auth_headers).json()

        r = client.post("/shopping-list", json=[r1["id"], r2["id"]], headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert sorted(body["recipe_ids"]) == sorted([r1["id"], r2["id"]])

    def test_ingredients_merged_by_name_and_unit(self, client, auth_headers):
        """Both recipes have 'chicken 300g' and 'rice 200g' → merged to 600g/400g."""
        r1 = client.post("/recipes", json=make_recipe_payload("A"), headers=auth_headers).json()
        r2 = client.post("/recipes", json=make_recipe_payload("B"), headers=auth_headers).json()

        r = client.post("/shopping-list", json=[r1["id"], r2["id"]], headers=auth_headers)
        items = r.json()["items"]

        chicken = next(i for i in items if i["name"] == "chicken")
        assert chicken["total_quantity"] == 600.0
        assert chicken["unit"] == "g"

        rice = next(i for i in items if i["name"] == "rice")
        assert rice["total_quantity"] == 400.0

    def test_missing_recipe_returns_404(self, client, auth_headers):
        r = client.post("/shopping-list", json=[99999], headers=auth_headers)
        assert r.status_code == 404

    def test_single_recipe_shopping_list(self, client, auth_headers):
        created = client.post("/recipes", json=make_recipe_payload(), headers=auth_headers).json()
        r = client.post("/shopping-list", json=[created["id"]], headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()["items"]) == 2

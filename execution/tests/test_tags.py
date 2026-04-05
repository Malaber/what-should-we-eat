"""
test_tags.py — Tag listing tests.
"""

from execution.tests.helpers import make_recipe_payload


class TestTags:
    def test_tags_for_household(self, client, auth_headers):
        client.post("/recipes", json=make_recipe_payload(tags=["Italian", "Quick"]), headers=auth_headers)
        r = client.get("/tags", headers=auth_headers)
        assert r.status_code == 200
        names = [t["name"] for t in r.json()]
        assert "Italian" in names
        assert "Quick" in names

    def test_tags_empty_when_no_recipes(self, client, auth_headers):
        r = client.get("/tags", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_tags_scoped_to_household(self, client, auth_headers, second_user_headers):
        client.post("/recipes", json=make_recipe_payload(tags=["AliceTag"]), headers=auth_headers)
        client.post("/recipes", json=make_recipe_payload(tags=["BobTag"]), headers=second_user_headers)

        alice_tags = [t["name"] for t in client.get("/tags", headers=auth_headers).json()]
        bob_tags = [t["name"] for t in client.get("/tags", headers=second_user_headers).json()]

        assert "AliceTag" in alice_tags
        assert "BobTag" not in alice_tags
        assert "BobTag" in bob_tags
        assert "AliceTag" not in bob_tags

    def test_orphan_tags_cleaned_after_delete(self, client, auth_headers):
        """When the only recipe using a tag is deleted, the tag should be cleaned up."""
        created = client.post("/recipes", json=make_recipe_payload(tags=["Unique"]), headers=auth_headers).json()

        tags_before = [t["name"] for t in client.get("/tags", headers=auth_headers).json()]
        assert "Unique" in tags_before

        client.delete(f"/recipes/{created['id']}", headers=auth_headers)

        tags_after = [t["name"] for t in client.get("/tags", headers=auth_headers).json()]
        assert "Unique" not in tags_after

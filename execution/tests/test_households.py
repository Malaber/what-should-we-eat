"""
test_households.py — Household CRUD, join, switch, and leave tests.
"""

from execution.tests.helpers import make_recipe_payload


class TestListHouseholds:
    def test_list_returns_personal_household(self, client, auth_headers):
        r = client.get("/households", headers=auth_headers)
        assert r.status_code == 200
        households = r.json()
        assert len(households) == 1
        assert "invite_code" in households[0]


class TestCreateHousehold:
    def test_create_household(self, client, auth_headers):
        r = client.post("/households", json={"name": "Family Kitchen"}, headers=auth_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Family Kitchen"
        assert len(body["invite_code"]) == 6

    def test_create_household_adds_to_list(self, client, auth_headers):
        client.post("/households", json={"name": "New One"}, headers=auth_headers)
        r = client.get("/households", headers=auth_headers)
        assert len(r.json()) == 2


class TestJoinHousehold:
    def test_join_by_invite_code(self, client, auth_headers, second_user_headers):
        # Alice creates a household
        h = client.post("/households", json={"name": "Shared"}, headers=auth_headers).json()
        invite_code = h["invite_code"]

        # Bob joins it
        r = client.post(f"/households/join/{invite_code}", headers=second_user_headers)
        assert r.status_code == 200
        assert r.json()["active_household_id"] == h["id"]

    def test_join_invalid_code_returns_404(self, client, auth_headers):
        r = client.post("/households/join/XXXXXX", headers=auth_headers)
        assert r.status_code == 404

    def test_join_is_idempotent(self, client, auth_headers, second_user_headers):
        """Joining the same household twice should not error."""
        h = client.post("/households", json={"name": "Shared"}, headers=auth_headers).json()
        code = h["invite_code"]

        r1 = client.post(f"/households/join/{code}", headers=second_user_headers)
        r2 = client.post(f"/households/join/{code}", headers=second_user_headers)
        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_join_case_insensitive(self, client, auth_headers, second_user_headers):
        h = client.post("/households", json={"name": "Test"}, headers=auth_headers).json()
        code_lower = h["invite_code"].lower()

        r = client.post(f"/households/join/{code_lower}", headers=second_user_headers)
        assert r.status_code == 200


class TestSwitchHousehold:
    def test_switch_to_member_household(self, client, auth_headers):
        h = client.post("/households", json={"name": "Alt"}, headers=auth_headers).json()
        r = client.post(f"/households/switch/{h['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["active_household_id"] == h["id"]

    def test_switch_to_non_member_returns_403(self, client, auth_headers, second_user_headers):
        # Bob creates a household — Alice is not a member
        h = client.post("/households", json={"name": "Private"}, headers=second_user_headers).json()
        r = client.post(f"/households/switch/{h['id']}", headers=auth_headers)
        assert r.status_code == 403


class TestLeaveHousehold:
    def test_leave_non_personal_household(self, client, auth_headers):
        # Get Alice's personal household for comparison
        me = client.get("/users/me", headers=auth_headers).json()
        personal_id = me["personal_household_id"]

        # Create and switch to a new household
        h = client.post("/households", json={"name": "Temp"}, headers=auth_headers).json()
        client.post(f"/households/switch/{h['id']}", headers=auth_headers)

        # Leave it — should revert to personal
        r = client.post(f"/households/leave/{h['id']}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["active_household_id"] == personal_id

    def test_cannot_leave_personal_household(self, client, auth_headers):
        me = client.get("/users/me", headers=auth_headers).json()
        r = client.post(f"/households/leave/{me['personal_household_id']}", headers=auth_headers)
        assert r.status_code == 400

    def test_leave_non_member_returns_404(self, client, auth_headers):
        r = client.post("/households/leave/99999", headers=auth_headers)
        assert r.status_code == 404


class TestRecipeImportBetweenHouseholds:
    def test_import_recipes_from_household(self, client, auth_headers, second_user_headers):
        # Alice creates recipes in her household
        client.post("/recipes", json=make_recipe_payload("Dish A"), headers=auth_headers)
        client.post("/recipes", json=make_recipe_payload("Dish B"), headers=auth_headers)

        # Get Alice's household invite code
        households = client.get("/households", headers=auth_headers).json()
        invite_code = households[0]["invite_code"]

        # Bob imports Alice's recipes into his household
        r = client.post(f"/recipes/import/{invite_code}", headers=second_user_headers)
        assert r.status_code == 201
        assert r.json()["imported_count"] == 2

        # Bob now has 2 recipes
        bob_recipes = client.get("/recipes", headers=second_user_headers).json()
        assert len(bob_recipes) == 2

    def test_import_from_own_household_returns_400(self, client, auth_headers):
        households = client.get("/households", headers=auth_headers).json()
        code = households[0]["invite_code"]
        r = client.post(f"/recipes/import/{code}", headers=auth_headers)
        assert r.status_code == 400

    def test_import_invalid_code_returns_404(self, client, auth_headers):
        r = client.post("/recipes/import/XXXXXX", headers=auth_headers)
        assert r.status_code == 404

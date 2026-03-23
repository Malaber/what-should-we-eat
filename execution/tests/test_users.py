"""
test_users.py — Smoke tests for the User API.

Usage:
    # Start the stack first, then:
    python -m execution.tests.test_users
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

    test_email = "test.user@example.com"
    test_password = "supersecretpassword123!"

    # ── Register User ────────────────────────────────────────────────
    print("\n📝 Register User")
    user_data = {
        "email": test_email,
        "name": "Test User",
        "password": test_password,
        "is_active": True,
        "is_admin": False
    }
    r = c.post("/users/register", json=user_data)
    
    # If the user already exists from a previous test run, we can handle it
    if r.status_code == 400 and r.json().get("detail") == "Email already registered":
        print("  ⚠️ User already exists, proceeding to login...")
        passed_register = True
    else:
        check("POST /users/register → 201", r.status_code == 201, f"id={r.json().get('id') if r.status_code == 201 else r.text}")
        if r.status_code == 201:
            body = r.json()
            check("Password not exposed in response", "password" not in body and "hashed_password" not in body)

    # ── Login (Get Token) ────────────────────────────────────────────
    print("\n🔑 Login (Get Token)")
    login_data = {
        "username": test_email,
        "password": test_password
    }
    # OAuth2PasswordRequestForm expects form data (x-www-form-urlencoded)
    r = c.post("/users/token", data=login_data)
    check("POST /users/token → 200", r.status_code == 200, "Should succeed with correct credentials")
    
    token_json = r.json()
    check("Returns access_token", "access_token" in token_json)
    access_token = token_json["access_token"]

    # ── Invalid Login ──────────────────────────────────────────────
    print("\n🚫 Invalid Login")
    invalid_login = {
        "username": test_email,
        "password": "wrongpassword"
    }
    r = c.post("/users/token", data=invalid_login)
    check("POST /users/token (wrong password) → 401", r.status_code == 401)

    # ── Get Current User ─────────────────────────────────────────────
    print("\n👤 Get /users/me")
    r = c.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    check("GET /users/me → 200", r.status_code == 200)
    user_me = r.json()
    check("Email matches", user_me.get("email") == test_email)

    # ── Unauthorized Request ─────────────────────────────────────────
    r = c.get("/users/me")
    check("GET /users/me without token → 401", r.status_code == 401)

    print("\n🏠 Households Integration")
    check("User has personal_household_id", "personal_household_id" in user_me)
    check("User has active_household_id", "active_household_id" in user_me)
    
    # 2nd user
    r2 = c.post("/users/register", json={"email": "u2@ex.com", "name": "U2", "password": "pw"})
    if r2.status_code == 201:
        u2 = r2.json()
    else:
        u2_tok = c.post("/users/token", data={"username": "u2@ex.com", "password": "pw"}).json()["access_token"]
        u2 = c.get("/users/me", headers={"Authorization": f"Bearer {u2_tok}"}).json()
        
    u2_house = u2["personal_household_id"]

    r_join = c.post(f"/households/join/{u2_house}", headers={"Authorization": f"Bearer {access_token}"})
    check("POST /households/join/{id} → 200", r_join.status_code == 200)
    check("Active household changed", r_join.json()["active_household_id"] == u2_house)

    r_leave = c.post("/households/leave", headers={"Authorization": f"Bearer {access_token}"})
    check("POST /households/leave → 200", r_leave.status_code == 200)
    check("Active household reverted", r_leave.json()["active_household_id"] == user_me["personal_household_id"])

    print("\n✅ All user smoke tests passed!\n")

if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"\n💥 {e}")
        sys.exit(1)

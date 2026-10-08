"""End-to-end WebAuthn with Chromium's virtual authenticator, no mocked proofs."""
from playwright.sync_api import Page, expect


def signup(page):
    page.goto(page.base_url + "/auth/login")
    page.locator("#registration summary").click()
    page.locator('[name="display_name"]').fill("Test User")
    page.locator('[name="email"]').fill("test@e2e.com")
    page.locator("#register button").click()
    expect(page.locator("#user-greeting")).to_contain_text("Hi, Test User")


def test_auth_gate_shown(page: Page):
    page.goto(page.base_url + "/")
    expect(page.locator("#login-gate")).to_be_visible()
    page.locator("#gate-login").click()
    expect(page.locator("#sign-in")).to_be_visible()
    expect(page.locator('input[type="password"]')).to_have_count(0)


def test_signup_logout_and_passkey_login(page: Page):
    signup(page)
    with page.expect_response("**/auth/logout") as response:
        page.locator("#btn-logout").click()
    assert response.value.status == 200
    expect(page.locator("#login-gate")).to_be_visible()
    page.locator("#gate-login").click()
    page.locator("#sign-in").click()
    expect(page.locator("#user-greeting")).to_contain_text("Hi, Test User")


def test_invalid_proof_shows_error(page: Page):
    page.goto(page.base_url + "/auth/login")
    page.evaluate("navigator.credentials.get = async () => ({id: 'unknown'})")
    page.locator("#sign-in").click()
    expect(page.locator("#error")).to_contain_text("Invalid passkey")


def test_cancelled_passkey_can_be_retried(page: Page):
    page.goto(page.base_url + "/auth/login")
    page.evaluate("() => { navigator.credentials.get = async () => { throw new DOMException('Cancelled', 'NotAllowedError'); }; }")
    page.locator("#sign-in").click()
    expect(page.locator("#error")).to_contain_text("cancelled")
    expect(page.locator("#sign-in")).to_be_enabled()

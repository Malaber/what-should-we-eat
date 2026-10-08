import pytest
from playwright.sync_api import Page, expect

def test_auth_gate_shown(page: Page):
    """Test that an unauthenticated user sees the login gate."""
    page.goto(page.base_url + "/")
    
    # Wait for JS to run and render the login gate
    gate = page.locator("#login-gate")
    expect(gate).to_be_visible()
    expect(gate.locator("h2")).to_have_text("Welcome!")
    
def test_signup_and_logout(page: Page):
    """Test signing up creates an account and hides the gate, then logging out shows it again."""
    page.goto(page.base_url + "/")
    
    # Open signup modal via gate
    page.locator("#gate-signup").click()
    
    signup_modal = page.locator("#signup-modal")
    expect(signup_modal).to_be_visible()
    
    # Fill in the form
    page.locator("#signup-name").fill("Test User")
    page.locator("#signup-email").fill("test@e2e.com")
    page.locator("#signup-password").fill("e2e-password-123")
    page.locator("#signup-form button[type='submit']").click(force=True)
    
    # Wait for the gate to disappear (implies successful login)
    expect(page.locator("#login-gate")).not_to_be_visible()
    
    # Check if user greeting is displayed
    greeting = page.locator("#user-greeting")
    expect(greeting).to_be_visible()
    expect(greeting).to_contain_text("Hi, Test User")
    
    # Now log out
    page.locator("#btn-logout").click()
    
    # Login gate should come back
    expect(page.locator("#login-gate")).to_be_visible()

def test_login_existing_user(page: Page):
    """Test logging in with an existing user works."""
    # We must create a user first (we can just register them directly through UI or API)
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator("#signup-email").fill("alice@e2e.com")
    page.locator("#signup-password").fill("alice-password-123")
    page.locator("#signup-form button[type='submit']").click()
    expect(page.locator("#login-gate")).not_to_be_visible()
    
    # Log out
    page.locator("#btn-logout").click()
    expect(page.locator("#login-gate")).to_be_visible()
    
    # Now log back in
    page.locator("#gate-login").click()
    login_modal = page.locator("#login-modal")
    expect(login_modal).to_be_visible()
    
    page.locator("#login-email").fill("alice@e2e.com")
    page.locator("#login-password").fill("alice-password-123")
    page.locator("#login-form button[type='submit']").click(force=True)
    
    expect(login_modal).not_to_be_visible()
    expect(page.locator("#login-gate")).not_to_be_visible()
    
def test_login_invalid_credentials(page: Page):
    """Test logging in with bad credentials shows an error."""
    page.goto(page.base_url + "/")
    page.locator("#gate-login").click()
    
    page.locator("#login-email").fill("nobody@e2e.com")
    page.locator("#login-password").fill("wrongpassword")
    page.locator("#login-form button[type='submit']").click(force=True)
    
    error = page.locator("#login-error")
    expect(error).to_be_visible()
    # The message comes from the backend

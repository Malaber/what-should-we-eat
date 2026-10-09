import pytest
from playwright.sync_api import Page, expect

def login_as_main_user(page: Page):
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator("#registration summary").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("main@e2e.com")
    page.locator("#register button").click()
    expect(page.locator("#user-greeting")).to_be_visible()

def login_as_second_user(page: Page):
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator("#registration summary").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("second@e2e.com")
    page.locator("#register button").click()
    expect(page.locator("#user-greeting")).to_be_visible()

def test_household_flows(page: Page, context):
    """Test generating a new household, grabbing its invite code, and having another user join it."""
    login_as_main_user(page)
    
    page.goto(page.base_url + "/households.html")
    
    # Create new household
    page.locator("#btn-create-household").click()
    page.locator("#create-name").fill("Cozy Kitchen")
    page.locator("#create-form button[type='submit']").click()
    
    expect(page.locator("#hh-toast")).to_contain_text("Created \"Cozy Kitchen\"!")
    
    # Switch to the new household
    households = page.locator(".hh-card")
    expect(households).to_have_count(2)  # Personal + Cozy Kitchen
    
    # Extract invite code
    cozy_card = households.filter(has_text="Cozy Kitchen")
    code_text = cozy_card.locator(".hh-card-id").inner_text()
    invite_code = code_text.replace("Code: ", "").strip()
    
    # Log out by creating a new page and clearing state (or using auth helpers)
    page.goto(page.base_url + "/")
    page.locator("#btn-logout").click()
    
    # Second user joins
    login_as_second_user(page)
    page.goto(page.base_url + "/households.html")
    
    page.locator("#btn-join-household").click()
    page.locator("#join-code").fill(invite_code)
    page.locator("#join-form button[type='submit']").click()
    
    expect(page.locator("#hh-toast")).to_contain_text("Joined household!")
    
    expect(households).to_have_count(2) # Second user's Personal + Shared Cozy
    expect(households.filter(has_text="Cozy Kitchen")).to_be_visible()

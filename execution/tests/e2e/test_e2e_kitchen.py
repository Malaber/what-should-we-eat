import pytest
from playwright.sync_api import Page, expect

def login_as_test_user(page: Page):
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator("#signup-email").fill("kitchen@e2e.com")
    page.locator("#signup-password").fill("kitchen-password")
    page.locator("#signup-form button[type='submit']").click(force=True)
    expect(page.locator("#user-greeting")).to_be_visible()

def create_recipe_and_roll(page: Page):
    page.goto(page.base_url + "/recipes.html")
    page.locator("#btn-create-recipe").click()
    page.locator("#recipe-name").fill("Kitchen Test Recipe")
    page.locator("#recipe-active-time").fill("10")
    
    # Add ingredient
    page.locator(".ingredient-row .ing-name").first.fill("Test Ingredient")
    page.locator(".ingredient-row .ing-qty").first.fill("500")
    page.locator(".ingredient-row .ing-unit").first.fill("g")
    
    # Add step
    page.locator(".step-row .step-desc").first.fill("First cook it.")
    page.locator(".step-row .step-dur").first.fill("10")
    
    page.locator("#btn-save-recipe").click()
    expect(page.locator("#toast")).to_contain_text("Recipe created!")
    
    page.goto(page.base_url + "/")
    page.locator("#recipe-count").fill("1")
    page.locator("#btn-roll").click()
    expect(page.locator(".recipe-card")).to_have_count(1)

def test_kitchen_empty_state(page: Page):
    """Test that kitchen shows empty state when no meals are planned."""
    login_as_test_user(page)
    page.goto(page.base_url + "/kitchen.html")
    
    empty_state = page.locator("#empty-state")
    expect(empty_state).to_be_visible()

def test_kitchen_cooked_flow(page: Page):
    """Test viewing a recipe in kitchen and marking it cooked."""
    login_as_test_user(page)
    create_recipe_and_roll(page)
    
    page.goto(page.base_url + "/kitchen.html")
    
    # Empty state should be hidden
    expect(page.locator("#empty-state")).not_to_be_visible()
    
    # Card should be visible
    card = page.locator(".recipe-card")
    expect(card).to_be_visible()
    expect(card.locator("h3")).to_have_text("Kitchen Test Recipe")
    
    # Click to open modal
    card.click()
    modal = page.locator("#meal-modal")
    expect(modal).to_be_visible()
    
    # Verify contents
    expect(modal.locator("#modal-title")).to_have_text("Kitchen Test Recipe")
    expect(modal.locator("#modal-ingredients")).to_contain_text("500 g Test Ingredient")
    expect(modal.locator("#modal-instructions")).to_contain_text("First cook it.")
    
    # Mark cooked
    cooked_btn = page.locator("#btn-toggle-cooked")
    cooked_btn.click()
    
    # Wait for modal to close on marking cooked
    expect(modal).not_to_be_visible()
    
    import re
    expect(card).to_have_class(re.compile(r"cooked-card"))

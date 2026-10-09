import pytest
from playwright.sync_api import Page, expect

def login_as_test_user(page: Page):
    """Helper to log in reliably."""
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator("#registration summary").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("meals@e2e.com")
    page.locator("#register button").click()
    expect(page.locator("#user-greeting")).to_be_visible()

def create_recipe(page: Page, name: str, kcal: str, time: str, tag: str):
    page.goto(page.base_url + "/recipes.html")
    page.locator("#btn-create-recipe").click()
    page.locator("#recipe-name").fill(name)
    if kcal: page.locator("#recipe-kcal").fill(kcal)
    if time: page.locator("#recipe-total-time").fill(time)
    
    page.locator("#new-tag-input").fill(tag)
    page.keyboard.press("Enter")
    
    page.locator("#btn-save-recipe").click()
    expect(page.locator("#toast")).to_contain_text("Recipe created!")

def test_meal_planning(page: Page):
    """Test generating a meal plan from selected filters."""
    login_as_test_user(page)
    
    # We must have some recipes in the DB to roll
    create_recipe(page, "Pasta", "500", "20", "Italian")
    create_recipe(page, "Pizza", "800", "30", "Italian")
    create_recipe(page, "Burger", "900", "15", "American")
    
    # Go back to main page
    page.goto(page.base_url + "/")
    
    # Wait for tags to load
    tag_locator = page.locator(".tag-pill", has_text="Italian")
    expect(tag_locator).to_be_visible()
    
    # Filter by Italian and roll 2 recipes
    tag_locator.click()
    page.locator("#recipe-count").fill("2")
    page.locator("#btn-roll").click()
    
    # Check that recipes are displayed
    recipes_section = page.locator("#recipes-section")
    expect(recipes_section).to_be_visible()
    
    # We should have exactly 2 recipe cards
    cards = page.locator(".recipe-card")
    expect(cards).to_have_count(2)
    
    # Shopping list should also be populated
    shopping_section = page.locator("#shopping-section")
    expect(shopping_section).to_be_visible()
    
    # Try the reroll single feature
    first_recipe_text = cards.first.locator("h3").inner_text()
    cards.first.locator("[data-reroll]").click()
    
    # Wait for the toast (either success or not enough recipes, since we only have 2 Italian and rolled 2)
    # The API will say no other recipes
    expect(page.locator("#toast")).to_contain_text("No other recipes available")
    
    # Try clearing the plan
    page.locator("#btn-reroll-all").click()
    expect(recipes_section).not_to_be_visible()

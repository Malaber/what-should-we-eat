import pytest
from playwright.sync_api import Page, expect

def login_as_test_user(page: Page):
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("kitchen@e2e.com")
    page.locator("#gate-register button").click()
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


def test_equipment_syncs_with_another_client_and_retries_offline_change(page: Page):
    login_as_test_user(page)
    account = page.evaluate("() => ({token: WSWEAuth.token, id: WSWEAuth.user.id})")
    headers = {"Authorization": f"Bearer {account['token']}"}
    api = page.request
    origin = page.base_url
    path = origin + "/users/me/equipment"
    recipe = api.post(origin + "/recipes", headers=headers, data={
        "name": "Cake", "equipment": ["Springform pan", "Chef knife"],
    }).json()
    assert api.post(origin + "/meal-plan/add", headers=headers, data={"recipe_ids": [recipe["id"]]}).ok
    assert api.put(path, headers=headers, data={"changes": {"Chef knife": True}}).ok
    page.evaluate("(id) => localStorage.setItem('onionary-equipment-v1-' + id, '[\"springform pan\"]')", account["id"])
    page.goto(origin + "/kitchen.html")
    with page.expect_response(lambda response: response.url == path and response.request.method == "PUT"):
        page.locator(".recipe-card").click()
    pan = page.get_by_role("checkbox", name="Springform pan")
    knife = page.get_by_role("checkbox", name="Chef knife")
    expect(pan).to_be_checked()
    expect(knife).to_be_checked()
    assert api.get(path, headers=headers).json() == {"owned": ["chef knife", "springform pan"]}

    page.route(path, lambda route: route.fulfill(status=503, body="Offline"))
    with page.expect_response(lambda response: response.url == path and response.status == 503):
        knife.uncheck()
    expect(page.locator("#modal-equipment-sync")).to_be_visible()
    assert api.get(path, headers=headers).json() == {"owned": ["chef knife", "springform pan"]}
    page.unroute(path)
    page.reload()
    with page.expect_response(lambda response: response.url == path and response.request.method == "PUT"):
        page.locator(".recipe-card").click()
    expect(knife).not_to_be_checked()
    expect(page.locator("#modal-equipment-sync")).to_be_hidden()
    assert api.get(path, headers=headers).json() == {"owned": ["springform pan"]}

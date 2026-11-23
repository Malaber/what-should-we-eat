import pytest
from playwright.sync_api import Page, expect


def test_shopping_header_contrast_and_copy_label(page: Page):
    login_as_test_user(page)
    create_recipe(page, "Pasta", "", "", "Italian")
    page.goto(page.base_url + "/")
    page.locator("#recipe-count").fill("1")
    page.locator("#btn-roll").click()
    toolbar = page.locator(".shopping-card-header")
    expect(toolbar).to_be_visible()

    for scheme in ("light", "dark"):
        page.emulate_media(color_scheme=scheme)
        page.set_viewport_size({"width": 360 if scheme == "dark" else 1200, "height": 800})
        expect(toolbar.get_by_role("heading")).to_be_visible()
        expect(toolbar.locator("#shop-badge")).to_be_visible()
        expect(toolbar.locator("#btn-copy-shopping .btn-text")).to_be_visible()
        ratios = toolbar.evaluate("""header => {
          const luminance = color => {
            const channels = color.match(/[0-9.]+/g).slice(0, 3).map(channel => {
              const s = Number(channel) / 255;
              return s <= .04045 ? s / 12.92 : ((s + .055) / 1.055) ** 2.4;
            });
            return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2];
          };
          const back = getComputedStyle(header).backgroundColor;
          return ['h2', '#shop-badge', '#btn-copy-shopping'].map(selector => {
            const style = getComputedStyle(header.querySelector(selector));
            const foreground = luminance(style.color);
            const background = luminance(selector === 'h2' ? back : style.backgroundColor);
            return (Math.max(foreground, background) + .05) / (Math.min(foreground, background) + .05);
          });
        }""")
        assert min(ratios) >= 4.5, (scheme, ratios)
        assert toolbar.evaluate("header => header.scrollWidth === header.clientWidth")

def login_as_test_user(page: Page):
    """Helper to log in reliably."""
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("meals@e2e.com")
    page.locator("#gate-register button").click()
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

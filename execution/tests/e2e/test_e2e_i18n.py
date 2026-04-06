import pytest
from playwright.sync_api import Page, expect

def test_language_switch(page: Page):
    """Test switching languages via the UI updates text and saves preference."""
    page.goto(page.base_url + "/")
    # Force mock localstorage to empty first just in case
    page.evaluate("window.localStorage.setItem('app_lang', 'en')")
    page.reload()
    
    # Verify the language switcher exists
    lang_switcher = page.locator("#lang-switcher")
    expect(lang_switcher).to_be_visible()
    expect(lang_switcher).to_have_value("en")
    
    # Check default english
    nav_link = page.locator(".nav-link[data-i18n='nav.pick_meals']")
    expect(nav_link).to_have_text("Pick Meals")
    expect(page.locator("h1")).to_contain_text("What Should We Eat?")
    
    # Switch to German
    lang_switcher.select_option("de")
    
    # Check if UI updated
    expect(nav_link).to_have_text("Gerichte planen")
    expect(page.locator("h1")).to_contain_text("Was sollen Wir Essen?")
    
    # Reload and test persistence
    page.reload()
    expect(lang_switcher).to_have_value("de")
    expect(nav_link).to_have_text("Gerichte planen")
    
    # Switch back to English to leave state clean
    lang_switcher.select_option("en")
    expect(nav_link).to_have_text("Pick Meals")

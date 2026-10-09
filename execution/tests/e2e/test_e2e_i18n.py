from playwright.sync_api import Page, expect
from execution.tests.e2e.test_e2e_recipes import login_as_test_user


def test_language_switch(page: Page):
    login_as_test_user(page)
    page.goto(page.base_url + '/auth/account')
    language = page.locator('#account-language')
    expect(language).to_have_value('system')
    language.select_option('de')
    expect(page.locator('h1')).to_have_text('Kontoeinstellungen')
    page.reload()
    expect(language).to_have_value('de')
    page.locator('#account-appearance').select_option('dark')
    expect(page.locator('html')).to_have_attribute('data-appearance', 'dark')
    page.locator('#profile-name').fill('Daniel Schädler')
    page.locator('#profile-form button').click()
    expect(page.locator('#status')).to_have_text('Konto aktualisiert.')
    page.reload()
    expect(page.locator('#profile-name')).to_have_value('Daniel Schädler')
    expect(page.locator('#keys button').last).to_be_disabled()
    expect(page.locator('#delete-all')).to_have_count(0)
    page.goto(page.base_url + '/recipes.html')
    expect(page.locator('#lang-switcher')).to_have_count(0)
    expect(page.locator('.nav-link[data-i18n="nav.pick_meals"]')).to_have_text('Gerichte planen')

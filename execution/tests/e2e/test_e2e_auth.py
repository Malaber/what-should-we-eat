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


def test_manage_passkeys_with_real_webauthn(page: Page):
    signup(page)
    page.goto(page.base_url + '/auth/security')
    page.locator('#keys button').filter(has_text='Rename').first.click()
    page.locator('#key-name').fill('Kitchen phone')
    page.locator('#action-form button[type=submit]').click()
    expect(page.locator('#keys')).to_contain_text('Kitchen phone')
    # Adding a backup key uses a second authenticator: the existing credential
    # is deliberately excluded from registration by the server.
    def use_second_authenticator(route):
        response = route.fetch()
        page.cdp.send('WebAuthn.removeVirtualAuthenticator', {'authenticatorId': page.authenticator_id})
        page.cdp.send('WebAuthn.addVirtualAuthenticator', {'options': {
            'protocol':'ctap2', 'transport':'internal', 'hasResidentKey':True,
            'hasUserVerification':True, 'isUserVerified':True, 'automaticPresenceSimulation':True}})
        route.fulfill(response=response)
    page.route('**/auth/passkeys/action/verify', use_second_authenticator, times=1)
    page.locator('#add').click()
    page.locator('#key-name').fill('Backup key')
    page.locator('#action-form button[type=submit]').click()
    expect(page.locator('#keys section')).to_have_count(2)
    page.locator('#keys section').filter(has_text='Kitchen phone').get_by_role('button', name='Delete…', exact=True).click()
    page.locator('#action-form button[type=submit]').click()
    expect(page.locator('#keys section')).to_have_count(1)
    page.locator('#delete-all').click()
    page.locator('#confirmation').fill('DELETE ALL PASSKEYS')
    page.locator('#action-form button[type=submit]').click()
    expect(page.locator('#sign-in')).to_be_visible()


def test_auth_theme_follows_system(page: Page):
    for mode in ('light', 'dark'):
        page.emulate_media(color_scheme=mode)
        page.goto(page.base_url + '/')
        gate_background = page.locator('#login-gate').evaluate('(el) => getComputedStyle(el).backgroundColor')
        page.locator('#gate-login').click()
        expect(page.locator('h1')).to_have_text('Welcome to Onionary.')
        assert page.locator('body').evaluate('(el) => getComputedStyle(el).backgroundColor') == gate_background
        page.screenshot(path=f'.tmp/onionary-signin-{mode}.png', full_page=True)

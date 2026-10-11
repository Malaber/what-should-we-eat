"""Operator tasks must work with scripts and styles unavailable."""
from datetime import timedelta
import secrets
import re
import pytest
from playwright.sync_api import expect
from execution.db.models import User, Household, HouseholdMember
from execution.db.passkeys import AuthSession
from execution.api.routers.passkeys import digest, now


@pytest.mark.parametrize("styles_enabled,scripts_enabled", [(True, True), (True, False), (False, False)])
def test_admin_native_forms(browser, browser_context_args, server_url, reset_db_data, styles_enabled, scripts_enabled):
    token = secrets.token_urlsafe(32)
    with reset_db_data() as db:
        home = Household(name='Admin kitchen', invite_code='admin-demo'); db.add(home); db.flush()
        admin = User(email='admin@example.org', name='Admin Cook', hashed_password='!passkey-only', is_admin=True,
                     is_active=True, personal_household_id=home.id, active_household_id=home.id)
        db.add(admin); db.flush()
        db.add(HouseholdMember(household_id=home.id, user_id=admin.id))
        db.add(AuthSession(token_hash=digest(token), user_id=admin.id, expires_at=now()+timedelta(days=1))); db.commit()
    context = browser.new_context(**{**browser_context_args, "java_script_enabled": scripts_enabled})
    context.add_cookies([{'name':'onionary_session','value':token,'url':server_url}])
    if not styles_enabled:
        context.route('**/*', lambda route: route.abort() if route.request.resource_type in {'stylesheet','font','script'} else route.continue_())
    page = context.new_page()
    page.goto(server_url+'/admin/user/list')
    if styles_enabled:
        expect(page.locator('table')).to_have_css('border-collapse', 'collapse')
    row = page.get_by_role('row').filter(has_text='admin@example.org')
    expect(row.get_by_role('cell', name='Yes', exact=True)).to_have_count(2)
    expect(row.get_by_role('link', name='Details / passkey link')).to_be_visible()
    page.get_by_role('link', name='New Account', exact=True).click()
    page.get_by_label('Email', exact=True).fill('review@example.org')
    page.get_by_label('Name', exact=True).fill('Review Cook')
    page.get_by_role('button', name='Create account', exact=True).click()
    assert page.url.endswith('/admin/user/list'), page.locator('body').inner_text()
    page.get_by_role('row').filter(has_text='review@example.org').get_by_role('link', name='Details / passkey link').click()
    page.get_by_label('Valid for (hours, 1–720)').fill('48')
    if scripts_enabled:
        page.get_by_role('button', name='Create passkey link').click()
    else:
        # Exercise native keyboard submission as well as the normal pointer path.
        page.get_by_label('Valid for (hours, 1–720)').press('Tab')
        expect(page.get_by_role('button', name='Create passkey link')).to_be_focused()
        page.keyboard.press('Enter')
    expect(page.locator('#generated-link')).to_have_value(re.compile(re.escape(server_url) + r'/auth/login#enroll=[A-Za-z0-9_-]+&identifier=[A-Za-z0-9_-]+'))
    page.get_by_role('link', name='View passkey links').click()
    page.get_by_role('link', name='Details / revoke').click()
    page.get_by_role('button', name='Revoke link').click()
    expect(page.get_by_role('button', name='Revoke link')).to_have_count(0)
    context.close()

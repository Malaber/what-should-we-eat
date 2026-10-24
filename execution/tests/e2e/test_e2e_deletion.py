from datetime import timedelta
import pytest
from playwright.sync_api import expect
from execution.db.models import User, Household, HouseholdMember
from execution.db.passkeys import AuthSession
from execution.api.routers.passkeys import digest, now


@pytest.mark.parametrize("enhanced", [True, False])
def test_deletion_native_form(browser, browser_context_args, server_url, reset_db_data, enhanced):
    with reset_db_data() as db:
        home = Household(name='Deletion kitchen', invite_code='delete'); db.add(home); db.flush()
        user = User(email='delete@example.org', name='Delete Cook', hashed_password='!passkey-only',
                    personal_household_id=home.id, active_household_id=home.id)
        db.add(user); db.flush()
        db.add(HouseholdMember(user_id=user.id, household_id=home.id))
        db.add(AuthSession(token_hash=digest('delete-browser'), user_id=user.id, expires_at=now()+timedelta(days=1)))
        db.commit()
    context = browser.new_context(**{**browser_context_args, 'java_script_enabled':enhanced, 'color_scheme':'dark'})
    context.add_cookies([{'name':'onionary_session', 'value':'delete-browser', 'url':server_url}])
    if not enhanced:
        context.route('**/*.css', lambda route: route.abort())
    page = context.new_page()
    page.goto(server_url+'/auth/security')
    page.get_by_role('link', name='Permanently delete account').click()
    expect(page.get_by_text('delete@example.org', exact=True)).to_be_visible()
    page.get_by_label('Type your account email to confirm').fill('wrong@example.org')
    page.get_by_role('button', name='Permanently delete account').click()
    expect(page.get_by_role('alert')).to_contain_text('does not match')
    page.get_by_label('Type your account email to confirm').fill('delete@example.org')
    page.get_by_role('button', name='Permanently delete account').click()
    expect(page.get_by_role('heading', name='Account deleted')).to_be_visible()
    with reset_db_data() as db:
        assert db.query(User).count() == 0
    context.close()

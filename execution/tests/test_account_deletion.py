from datetime import datetime, timedelta, timezone
from execution.db.database import SessionLocal
from execution.db.models import User, Household, HouseholdMember, Recipe
from execution.db.passkeys import AuthSession, AuthFlow, Passkey, PasskeyAddLink


def test_confirmation_and_authorization(client, auth_headers):
    assert client.post('/users/me/delete', json={'email': 'alice@test.com'}).status_code == 401
    assert client.post('/users/me/delete', headers=auth_headers, json={'email': 'wrong@test.com'}).status_code == 400
    assert client.get('/users/me', headers=auth_headers).status_code == 200


def test_permanent_cleanup(client, auth_headers):
    with SessionLocal() as db:
        user = db.query(User).one()
        hid = user.personal_household_id
        db.add(Recipe(household_id=hid, name='Private'))
        db.add(AuthSession(token_hash='session', user_id=user.id, expires_at=datetime.now(timezone.utc)+timedelta(days=1)))
        db.add(AuthFlow(token_hash='flow', kind='refresh', payload={'user_id':user.id}, expires_at=datetime.now(timezone.utc)))
        db.add(Passkey(credential_id='key', user_id=user.id, public_key=b'key', sign_count=0))
        db.add(PasskeyAddLink(user_id=user.id, created_by=user.id, token_hash='link', expires_at=datetime.now(timezone.utc)))
        db.commit()
    assert client.post('/users/me/delete', headers=auth_headers, json={'email':' ALICE@test.com '}).status_code == 204
    assert client.get('/users/me', headers=auth_headers).status_code == 401
    with SessionLocal() as db:
        for model in (User, Household, HouseholdMember, Recipe, AuthSession, AuthFlow, Passkey, PasskeyAddLink):
            assert db.query(model).count() == 0


def test_shared_kitchen_survives(client, auth_headers, second_user_headers):
    with SessionLocal() as db:
        alice = db.query(User).filter_by(email='alice@test.com').one()
        bob = db.query(User).filter_by(email='bob@test.com').one()
        db.add(HouseholdMember(user_id=bob.id, household_id=alice.personal_household_id))
        db.add(Recipe(household_id=alice.personal_household_id, name='Shared'))
        db.commit()
    assert client.post('/users/me/delete', headers=auth_headers, json={'email':'alice@test.com'}).status_code == 204
    assert client.get('/users/me', headers=second_user_headers).status_code == 200
    with SessionLocal() as db:
        assert db.query(Recipe).one().name == 'Shared'
        assert db.query(User).one().email == 'bob@test.com'


def browser_session(client):
    from execution.api.routers.passkeys import digest
    with SessionLocal() as db:
        user = db.query(User).filter_by(email='alice@test.com').one()
        db.add(AuthSession(token_hash=digest('browser'), user_id=user.id,
                           expires_at=datetime.now(timezone.utc)+timedelta(days=1)))
        db.commit()
    client.cookies.set('onionary_session', 'browser')


def test_native_browser_form_and_csrf(client, auth_headers):
    browser_session(client)
    page = client.get('/auth/account/delete?lang=de')
    assert page.status_code == 200
    assert 'Konto dauerhaft löschen' in page.text
    assert '<form method="post"' in page.text
    assert '<label for="email">' in page.text
    endpoint = '/auth/account/delete/confirm'
    assert client.post(endpoint, data={'email':'alice@test.com'}).status_code == 403
    headers = {'Origin':'http://localhost:8000'}
    assert client.post(endpoint, headers=headers, data={'email':'wrong@test.com'}).status_code == 400
    assert client.get('/users/me', headers=auth_headers).status_code == 200
    response = client.post(endpoint, headers=headers, data={'email':'alice@test.com'})
    assert response.status_code == 200
    assert 'Account deleted' in response.text
    assert 'Max-Age=0' in response.headers['set-cookie']
    assert client.get('/users/me', headers=auth_headers).status_code == 401


def test_browser_json_deletion_requires_origin(client, auth_headers):
    browser_session(client)
    assert client.post('/auth/account/delete', json={'email':'alice@test.com'}).status_code == 403
    assert client.post('/auth/account/delete', headers={'Origin':'http://localhost:8000'},
                       json={'email':'alice@test.com'}).json() == {'deleted':True}

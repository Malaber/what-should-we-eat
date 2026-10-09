from types import SimpleNamespace
import re

import pytest
from fastpasskey import FastPasskey
from bs4 import BeautifulSoup

from execution.tests.test_passkeys import ORIGIN, register, verified_registration
from execution.db.database import SessionLocal
from execution.db.models import User
from execution.db.passkeys import Passkey, PasskeyAddLink, AuthSession
from execution.passkey_links import issue_link
from execution.api.routers.passkeys import digest, now


@pytest.fixture
def owner(client, verified_registration, monkeypatch):
    assert register(client).status_code == 200
    monkeypatch.setattr(FastPasskey, 'verify_authentication', lambda *a, **kw: SimpleNamespace(new_sign_count=kw['credential_current_sign_count'] + 1))
    with SessionLocal() as db:
        return db.query(Passkey).one().credential_id


def action(client, key, kind, **values):
    r = client.post('/auth/passkeys/action/options', headers=ORIGIN, json={'action': kind, **values})
    assert r.status_code == 200, r.text
    return client.post('/auth/passkeys/action/verify', headers=ORIGIN, json={'credential': {'id': key}})


def test_manage_add_rename_delete_and_confirm_all(client, owner, monkeypatch):
    assert client.get('/auth/passkeys').json()[0]['name'] == 'Passkey'
    r = action(client, owner, 'rename', key_id=owner, name='My phone')
    assert r.status_code == 200
    assert client.get('/auth/passkeys').json()[0]['name'] == 'My phone'
    assert action(client, owner, 'delete', key_id=owner).status_code == 400
    r = action(client, owner, 'add', name='Backup key')
    assert 'options' in r.json()
    monkeypatch.setattr(FastPasskey, 'verify_registration', lambda *a, **kw: SimpleNamespace(credential_id=b'backup-key', credential_public_key=b'key', sign_count=0))
    assert client.post('/auth/passkeys/register/verify', headers=ORIGIN, json={'credential': {}}).status_code == 200
    keys = client.get('/auth/passkeys').json()
    backup = next(k['id'] for k in keys if k['name'] == 'Backup key')
    assert action(client, owner, 'delete', key_id=backup).status_code == 200
    assert client.post('/auth/passkeys/action/options', headers=ORIGIN, json={'action':'delete_all'}).status_code == 400
    assert action(client, owner, 'delete_all', confirmation='DELETE ALL PASSKEYS').status_code == 200
    assert client.get('/auth/passkeys').status_code == 401
    with SessionLocal() as db:
        assert db.query(Passkey).count() == 0
        assert db.query(AuthSession).count() == 0
        assert db.query(User).count() == 1


def test_management_requires_origin_and_cannot_replay(client, owner):
    assert client.post('/auth/passkeys/action/options', json={'action':'add'}).status_code == 403
    assert action(client, owner, 'rename', key_id=owner, name='Phone').status_code == 200
    assert client.post('/auth/passkeys/action/verify', headers=ORIGIN, json={'credential':{'id':owner}}).status_code == 401
    assert client.post('/auth/passkeys/action/options', headers=ORIGIN, json={'action':'delete', 'key_id':'someone-else'}).status_code == 404


def test_failed_replace_preserves_old_keys(client, owner, monkeypatch):
    assert action(client, owner, 'replace', name='New key').status_code == 200
    monkeypatch.setattr(FastPasskey, 'verify_registration', lambda *a, **kw: (_ for _ in ()).throw(ValueError('bad proof')))
    assert client.post('/auth/passkeys/register/verify', headers=ORIGIN, json={'credential':{}}).status_code == 400
    assert client.get('/auth/passkeys').json()[0]['id'] == owner


def test_review_link_survives_cancel_and_consumes_on_success(client, owner, monkeypatch):
    with SessionLocal() as db:
        token, link = issue_link(db, db.query(User).one(), hours=720)
        link_id = link.id
    for _ in range(2):
        assert client.post('/auth/enroll/options', headers=ORIGIN, json={'token':token}).status_code == 200
    monkeypatch.setattr(FastPasskey, 'verify_registration', lambda *a, **kw: SimpleNamespace(credential_id=b'reviewer-key', credential_public_key=b'key', sign_count=0))
    assert client.post('/auth/enroll/verify', headers=ORIGIN, json={'credential':{}}).status_code == 200
    assert client.post('/auth/enroll/options', headers=ORIGIN, json={'token':token}).status_code == 401
    with SessionLocal() as db:
        assert db.get(PasskeyAddLink, link_id).used_at is not None
        assert db.query(Passkey).count() == 2


def test_revocation_after_ceremony_start_blocks_enrollment(client, owner):
    with SessionLocal() as db:
        token, link = issue_link(db, db.query(User).one()); link_id = link.id
    assert client.post('/auth/enroll/options', headers=ORIGIN, json={'token':token}).status_code == 200
    with SessionLocal() as db:
        db.get(PasskeyAddLink, link_id).revoked_at = now(); db.commit()
    assert client.post('/auth/enroll/verify', headers=ORIGIN, json={'credential':{}}).status_code == 401


def test_sqladmin_access_csrf_creation_and_links(client, owner):
    assert client.get('/admin/').status_code == 403
    with SessionLocal() as db:
        user = db.query(User).one(); user.is_admin = True; db.commit()
    page = client.get('/admin/user/create')
    assert page.status_code == 200
    csrf = BeautifulSoup(page.text, 'html.parser').select_one('input[name=csrf]')['value']
    data = {'email':'review@example.com', 'name':'Review', 'save':'Save'}
    assert client.post('/admin/user/create', headers=ORIGIN, data=data).status_code == 403
    r = client.post('/admin/user/create', headers=ORIGIN, data={**data,'csrf':csrf})
    assert r.status_code == 200, r.text
    with SessionLocal() as db:
        review = db.query(User).filter_by(email='review@example.com').one()
        assert not review.is_admin
        review_id = review.id
    r = client.post(f'/admin/user/{review_id}/passkey-add-link', headers=ORIGIN, data={'csrf':csrf, 'hours':'720'})
    assert r.status_code == 200, r.text
    assert '#enroll=' in r.text
    with SessionLocal() as db:
        link = db.query(PasskeyAddLink).one(); link_id = link.id; token_hash = link.token_hash
    listing = client.get('/admin/passkey-add-link/list')
    assert token_hash not in listing.text
    details = client.get(f'/admin/passkey-add-link/details/{link_id}')
    assert token_hash not in details.text
    r = client.post(f'/admin/passkey-add-link/{link_id}/revoke', headers=ORIGIN, data={'csrf':csrf})
    assert r.status_code == 200
    with SessionLocal() as db:
        assert db.get(PasskeyAddLink, link_id).revoked_at is not None

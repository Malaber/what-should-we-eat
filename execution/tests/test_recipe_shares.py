from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import json
import pytest
from execution.tests.helpers import make_recipe_payload
from execution.db.database import SessionLocal
from execution.db.models import RecipeShare
from execution.recipe_sharing import share_location, public_addresses, fetch_snapshot, MAX_BYTES


def test_share_snapshot_copy_expiry_revocation_and_ownership(client, auth_headers, second_user_headers):
    recipe = client.post('/recipes', json=make_recipe_payload('Original'), headers=auth_headers).json()
    assert client.post('/recipe-shares', json={'recipe_id':recipe['id']}).status_code == 401
    assert client.post('/recipe-shares', json={'recipe_id':recipe['id']}, headers=second_user_headers).status_code == 404
    shared = client.post('/recipe-shares', json={'recipe_id':recipe['id'], 'hours':24}, headers=auth_headers).json()
    token = shared['url'].split('#')[1]
    client.put('/recipes/'+str(recipe['id']), json={'name':'Changed'}, headers=auth_headers)
    response = client.post('/recipe-shares/resolve', json={'token':token})
    assert response.headers['cache-control'] == 'no-store'
    assert response.json()['recipe']['name'] == 'Original'
    assert 'household_id' not in response.json()['recipe']
    assert 'id' not in response.json()['recipe']['ingredients'][0]
    with patch('execution.api.routers.recipe_shares.fetch_snapshot', return_value=__import__('execution.api.schemas', fromlist=['RecipeCreate']).RecipeCreate.model_validate(response.json()['recipe'])):
        preview = client.post('/recipe-shares/preview', json={'url':'https://remote.example/share.html#'+token}, headers=second_user_headers)
        copied = client.post('/recipes', json=preview.json(), headers=second_user_headers)
        assert copied.status_code == 201
        assert copied.json()['id'] != recipe['id']
        assert copied.json()['name'] == 'Original'
    assert client.delete('/recipe-shares/'+shared['id'], headers=second_user_headers).status_code == 404
    assert client.get('/recipe-shares', headers=second_user_headers).json() == []
    assert client.delete('/recipe-shares/'+shared['id'], headers=auth_headers).status_code == 204
    assert client.post('/recipe-shares/resolve', json={'token':token}).status_code == 404
    with SessionLocal() as db:
        row = db.get(RecipeShare, shared['id']); row.revoked_at = None; row.expires_at = datetime.now(timezone.utc)-timedelta(seconds=1); db.commit()
    assert client.post('/recipe-shares/resolve', json={'token':token}).status_code == 404

@pytest.mark.parametrize('url', ['http://public.example/share.html#'+'a'*43,'https://user:pass@example.org/share.html#'+'a'*43,'https://example.org/admin#'+'a'*43,'https://example.org/share.html?x=1#'+'a'*43,'https://example.org:8443/share.html#'+'a'*43])
def test_link_shape_rejected(url):
    with pytest.raises(ValueError): share_location(url)

@pytest.mark.parametrize('address', ['127.0.0.1','10.0.0.1','169.254.169.254','::1','::ffff:127.0.0.1'])
def test_private_dns_rejected(address):
    with patch('socket.getaddrinfo', return_value=[(2,1,6,'',(address,443))]):
        with pytest.raises(ValueError): public_addresses('public-looking.example')


def test_fetch_is_pinned_has_no_credentials_and_rejects_redirects():
    with patch('execution.recipe_sharing.public_addresses', return_value=['93.184.216.34']), patch('execution.recipe_sharing.PinnedHTTPSConnection') as cls:
        response = cls.return_value.getresponse.return_value
        response.status = 302
        with pytest.raises(ValueError): fetch_snapshot('https://example.org/share.html#'+'a'*43)
        cls.assert_called_once_with('example.org','93.184.216.34')
        args,kwargs = cls.return_value.request.call_args
        assert args == ('POST','/recipe-shares/resolve')
        assert set(kwargs['headers']) == {'Content-Type','Accept'}
        assert cls.return_value.close.called


def test_oversized_response_rejected():
    with patch('execution.recipe_sharing.public_addresses', return_value=['93.184.216.34']), patch('execution.recipe_sharing.PinnedHTTPSConnection') as cls:
        response=cls.return_value.getresponse.return_value;response.status=200
        response.getheader.return_value='application/json';response.read.return_value=b' '*(MAX_BYTES+1)
        with pytest.raises(ValueError, match='large'):fetch_snapshot('https://example.org/share.html#'+'a'*43)


def test_valid_remote_snapshot_returns_review_draft_without_saving():
    snapshot = {'format':'onionary.recipe.v1', 'recipe': make_recipe_payload('Remote soup')}
    with patch('execution.recipe_sharing.public_addresses', return_value=['93.184.216.34']), patch('execution.recipe_sharing.PinnedHTTPSConnection') as cls:
        response = cls.return_value.getresponse.return_value
        response.status = 200; response.getheader.return_value='application/json; charset=utf-8'
        response.read.return_value=json.dumps(snapshot).encode()
        draft=fetch_snapshot('https://example.org/share.html#'+'a'*43)
        assert draft.name == 'Remote soup'
        assert len(draft.ingredients) == 2

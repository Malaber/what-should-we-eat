import pytest
from execution.api.recipe_import import _parse_servings

def test_servings_round_trip(client, auth_headers):
    response = client.post('/recipes', json={'name': 'Soup', 'servings': 4.32}, headers=auth_headers)
    assert response.status_code == 201
    recipe = response.json()
    assert recipe['servings'] == 4.32
    assert client.put(f"/recipes/{recipe['id']}", json={'servings': 1.53}, headers=auth_headers).json()['servings'] == 1.53
    for invalid in [0, -1, None]:
        assert client.put(f"/recipes/{recipe['id']}", json={'servings': invalid}, headers=auth_headers).status_code == 422

@pytest.mark.parametrize('raw,expected', [('4 Portionen',4), (['4','Portionen'],4), ('1,5 servings',1.5), (None,1), ('0',1)])
def test_chefkoch_servings(raw, expected):
    assert _parse_servings(raw) == expected

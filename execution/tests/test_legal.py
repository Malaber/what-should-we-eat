import pytest
from fastapi.testclient import TestClient
from execution.api.main import app
from execution.legal import legal_identity

@pytest.mark.parametrize('name', ['IMPRESSUM_NAME', 'IMPRESSUM_ADDRESS', 'IMPRESSUM_EMAIL'])
def test_missing_identity_refuses_startup(monkeypatch, name):
    monkeypatch.delenv(name)
    with pytest.raises(RuntimeError, match=name):
        with TestClient(app):
            pass

def test_impressum_escapes_operator_values(client, monkeypatch):
    monkeypatch.setenv('IMPRESSUM_NAME', '<script>alert(1)</script>')
    monkeypatch.setenv('IMPRESSUM_ADDRESS', 'Street 1\nCity')
    response = client.get('/impressum.html')
    assert response.status_code == 200
    assert '&lt;script&gt;' in response.text
    assert '<script>alert(1)</script>' not in response.text
    assert 'Street 1\nCity' in response.text
    assert 'tobhuber' not in response.text

def test_invalid_email_refused(monkeypatch):
    monkeypatch.setenv('IMPRESSUM_EMAIL', 'bad\n@example.com')
    with pytest.raises(RuntimeError, match='IMPRESSUM_EMAIL'):
        legal_identity()


def test_impressum_preserves_umlauts(client, monkeypatch):
    monkeypatch.setenv('IMPRESSUM_NAME', 'Daniel Schädler')
    response = client.get('/impressum.html')
    assert 'Daniel Schädler' in response.text
    assert r'Sch\u00e4dler' not in response.text

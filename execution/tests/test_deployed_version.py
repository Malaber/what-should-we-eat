from execution.api.main import app


def test_version_reports_running_app_and_disables_cache(client, monkeypatch):
    monkeypatch.setattr(app, 'version', '0.3.0-dev.abc123')
    response = client.get('/version')
    assert response.json() == {'version': '0.3.0-dev.abc123'}
    assert response.headers['cache-control'] == 'no-store'

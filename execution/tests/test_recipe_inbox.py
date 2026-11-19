from execution.tests.test_account_deletion import browser_session


def test_native_browser_submission_syncs_to_same_account(client, auth_headers, second_user_headers):
    browser_session(client)
    page = client.get("/import-later", headers={"Accept-Language": "de"})
    assert page.status_code == 200
    assert "<form method=\"post\" action=\"/import-later\">" in page.text
    assert "Für iPhone vormerken" in page.text
    assert "no-store" in page.headers["Cache-Control"]

    source = {"kind": "url", "content": "https://other.onionary.example/share.html#" + "a" * 43}
    assert client.post("/import-later", data=source).status_code == 403
    response = client.post("/import-later", data=source, headers={"Origin": "http://localhost:8000"})
    assert response.status_code == 200
    assert "Import saved." in response.text
    inbox = client.get("/recipe-inbox", headers=auth_headers).json()
    assert [(item["kind"], item["content"]) for item in inbox] == [("url", source["content"])]
    assert client.post("/recipe-inbox", json=source, headers=auth_headers).json()["id"] == inbox[0]["id"]
    assert not client.get("/recipe-inbox", headers=second_user_headers).json()
    endpoint = f'/recipe-inbox/{inbox[0]["id"]}'
    assert client.delete(endpoint, headers=second_user_headers).status_code == 404
    assert client.delete(endpoint, headers=auth_headers).status_code == 204
    assert not client.get("/recipe-inbox", headers=auth_headers).json()


def test_recipe_text_and_invalid_links(client, auth_headers):
    assert client.get("/recipe-inbox").status_code == 401
    for url in ["http://example.com/a", "https://secret@example.com/a",
                "https://printer.local/a", "https://127.0.0.1", "https://example.com/a b"]:
        response = client.post("/recipe-inbox", headers=auth_headers, json={"kind": "url", "content": url})
        assert response.status_code == 422
    text = "Birnenkuchen\n\n40 g Butter\nZutaten mischen."
    result = client.post("/recipe-inbox", headers=auth_headers, json={"kind": "text", "content": f"  {text} "})
    assert result.status_code == 200
    assert result.json()["content"] == text
    assert client.post("/users/me/delete", headers=auth_headers, json={"email": "alice@test.com"}).status_code == 204

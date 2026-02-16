def test_signup_login_me(client):
    # signup
    r = client.post("/auth/signup", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    assert token

    # me
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "a@example.com"

    # login
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]

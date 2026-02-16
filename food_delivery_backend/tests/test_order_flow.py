def _auth_headers(client):
    r = client.post("/auth/signup", json={"email": "b@example.com", "password": "password123"})
    assert r.status_code in (201, 400)
    if r.status_code == 201:
        token = r.json()["access_token"]
    else:
        r = client.post("/auth/login", json={"email": "b@example.com", "password": "password123"})
        token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_browse_and_order_and_pay(client):
    headers = _auth_headers(client)

    r = client.get("/restaurants")
    assert r.status_code == 200, r.text
    restaurants = r.json()
    assert len(restaurants) >= 1
    rid = restaurants[0]["id"]

    r = client.get(f"/restaurants/{rid}/menu")
    assert r.status_code == 200, r.text
    menu = r.json()
    assert len(menu) >= 1
    item_id = menu[0]["id"]

    r = client.post("/cart/items", json={"menu_item_id": item_id, "quantity": 2}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["subtotal_cents"] > 0

    r = client.post("/orders", headers=headers)
    assert r.status_code == 200, r.text
    order = r.json()["order"]
    assert order["status"] == "CREATED"
    order_id = order["id"]

    r = client.post(f"/payments/intent/{order_id}", headers=headers)
    assert r.status_code == 200, r.text
    pi = r.json()["payment_intent"]
    assert pi["status"] == "REQUIRES_CONFIRMATION"

    r = client.post(f"/payments/confirm/{order_id}", json={"client_secret": pi["client_secret"]}, headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "SUCCEEDED"

    r = client.get(f"/orders/{order_id}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "CONFIRMED"

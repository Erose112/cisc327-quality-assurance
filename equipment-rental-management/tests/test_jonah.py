def test_renter_list_is_empty_initially(client):
    response = client.get("/renters")

    assert response.status_code == 200
    assert response.get_json() == []


def test_add_renter_returns_and_persists_expected_fields(client):
    response = client.post(
        "/renters",
        json={"name": "Jonah Smith", "email": "jonah@example.com"},
    )

    assert response.status_code == 201
    renter = response.get_json()
    assert renter["id"] == 1
    assert renter["name"] == "Jonah Smith"
    assert renter["email"] == "jonah@example.com"
    assert "membership_date" in renter

    list_response = client.get("/renters")
    assert list_response.status_code == 200
    assert list_response.get_json() == [renter]


def test_get_renter_returns_the_requested_record(client):
    create_response = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    )
    renter_id = create_response.get_json()["id"]

    response = client.get(f"/renters/{renter_id}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Alex Brown"
    assert response.get_json()["email"] == "alex@example.com"


def test_edit_renter_updates_and_persists_changes(client):
    create_response = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    )
    renter_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/renters/{renter_id}",
        json={"name": "Alex Green", "email": "alex.green@example.com"},
    )

    assert update_response.status_code == 200
    assert update_response.get_json()["name"] == "Alex Green"
    assert update_response.get_json()["email"] == "alex.green@example.com"

    get_response = client.get(f"/renters/{renter_id}")
    assert get_response.status_code == 200
    assert get_response.get_json()["name"] == "Alex Green"
    assert get_response.get_json()["email"] == "alex.green@example.com"


def test_delete_renter_removes_record_and_subsequent_get_returns_not_found(client):
    create_response = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    )
    renter_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/renters/{renter_id}")

    assert delete_response.status_code == 204
    assert delete_response.get_data() == b""

    get_response = client.get(f"/renters/{renter_id}")
    assert get_response.status_code == 404
    assert get_response.get_json() == {"error": "Renter not found"}

    list_response = client.get("/renters")
    assert list_response.status_code == 200
    assert list_response.get_json() == []


def test_renter_operations_for_missing_id_return_not_found(client):
    assert client.get("/renters/999").status_code == 404
    assert client.put(
        "/renters/999",
        json={"name": "Nobody", "email": "nobody@example.com"},
    ).status_code == 404
    assert client.delete("/renters/999").status_code == 404
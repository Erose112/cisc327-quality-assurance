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


def test_rental_list_is_empty_initially(client):
    response = client.get("/rentals")

    assert response.status_code == 200
    assert response.get_json() == []


def test_checkout_creates_rental_and_reduces_equipment_availability(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 2},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()

    response = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    )

    assert response.status_code == 201
    rental = response.get_json()
    assert rental["equipment_id"] == equipment["id"]
    assert rental["renter_id"] == renter["id"]
    assert rental["return_date"] is None
    assert rental["deposit_amount"] == 0.0
    assert rental["due_date"] is not None

    availability = client.get(f"/equipment/{equipment['id']}/availability")
    assert availability.status_code == 200
    assert availability.get_json()["available_units"] == 1


def test_rental_list_can_filter_by_equipment_id(client):
    first_equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()
    second_equipment = client.post(
        "/equipment",
        json={"name": "Bike", "category": "Cycles", "total_units": 1},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()

    client.post(
        "/rentals",
        json={"equipment_id": first_equipment["id"], "renter_id": renter["id"]},
    )
    client.post(
        "/rentals",
        json={"equipment_id": second_equipment["id"], "renter_id": renter["id"]},
    )

    response = client.get(f"/rentals?equipment_id={first_equipment['id']}")

    assert response.status_code == 200
    rentals = response.get_json()
    assert len(rentals) == 1
    assert rentals[0]["equipment_id"] == first_equipment["id"]


def test_rental_list_can_filter_by_renter_id(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 2},
    ).get_json()
    first_renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()
    second_renter = client.post(
        "/renters",
        json={"name": "Sam Green", "email": "sam@example.com"},
    ).get_json()

    client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": first_renter["id"]},
    )
    client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": second_renter["id"]},
    )

    response = client.get(f"/rentals?renter_id={first_renter['id']}")

    assert response.status_code == 200
    rentals = response.get_json()
    assert len(rentals) == 1
    assert rentals[0]["renter_id"] == first_renter["id"]


def test_checkout_for_missing_equipment_returns_not_found(client):
    response = client.post(
        "/rentals",
        json={"equipment_id": 999, "renter_id": 1},
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


def test_checkout_rejects_equipment_marked_unavailable(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()
    status_response = client.patch(
        f"/equipment/{equipment['id']}/status",
        json={"is_available": False},
    )

    response = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    )

    assert status_response.status_code == 200
    assert response.status_code == 400
    assert response.get_json() == {"error": "Equipment is out of service"}
    assert client.get("/rentals").get_json() == []


def test_checkout_rejects_equipment_with_no_available_units(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()
    first_response = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    )

    second_response = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.get_json() == {"error": "Equipment is not available"}
    assert len(client.get("/rentals").get_json()) == 1
    assert client.get(
        f"/equipment/{equipment['id']}/availability"
    ).get_json()["available_units"] == 0


def test_checkout_rejects_unknown_renter_without_creating_rental(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()

    response = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": 999},
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Renter not found"}
    assert client.get("/rentals").get_json() == []
    assert client.get(
        f"/equipment/{equipment['id']}/availability"
    ).get_json()["available_units"] == 1


def test_return_rental_sets_return_date_and_restores_availability(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()
    rental = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    ).get_json()

    response = client.put(f"/rentals/{rental['id']}/return")

    assert response.status_code == 200
    returned_rental = response.get_json()
    assert returned_rental["return_date"] is not None
    assert returned_rental["equipment_id"] == equipment["id"]

    availability = client.get(f"/equipment/{equipment['id']}/availability")
    assert availability.get_json()["available_units"] == 1


def test_return_persists_return_date_in_rental_list(client):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()
    rental = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    ).get_json()

    return_response = client.put(f"/rentals/{rental['id']}/return")
    rentals_response = client.get(f"/rentals?equipment_id={equipment['id']}")

    assert return_response.status_code == 200
    assert rentals_response.status_code == 200
    assert rentals_response.get_json()[0]["return_date"] is not None


def test_returning_rental_twice_returns_bad_request_without_double_restoring_availability(
    client,
):
    equipment = client.post(
        "/equipment",
        json={"name": "Kayak", "category": "Boats", "total_units": 1},
    ).get_json()
    renter = client.post(
        "/renters",
        json={"name": "Alex Brown", "email": "alex@example.com"},
    ).get_json()
    rental = client.post(
        "/rentals",
        json={"equipment_id": equipment["id"], "renter_id": renter["id"]},
    ).get_json()

    first_response = client.put(f"/rentals/{rental['id']}/return")
    second_response = client.put(f"/rentals/{rental['id']}/return")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.get_json() == {"error": "Rental already returned"}

    availability = client.get(f"/equipment/{equipment['id']}/availability")
    assert availability.get_json()["available_units"] == 1


def test_returning_missing_rental_returns_not_found(client):
    response = client.put("/rentals/999/return")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Rental not found"}
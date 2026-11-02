VALID_RENTAL_STATUSES = {"Available", "Rented", "On-Hold", "Overdue"}

# Helper function
def _create_equipment(client, name="Kayak", category="Water", total_units=2):
    response = client.post(
        "/equipment",
        json={"name": name, "category": category, "total_units": total_units},
    )
    assert response.status_code == 201
    return response.get_json()

# Feature - View/List Equipment
def test_list_equipment_returns_empty_list_initially(client):
    """Unauthenticated customers see an empty catalog when nothing is stored."""
    response = client.get("/equipment")
    assert response.status_code == 200
    assert response.get_json() == []

# Feature - View/List Equipment
def test_list_equipment_returns_created_items_with_persisted_fields(client):
    """POST then GET /equipment returns the same equipment with core fields."""
    created = _create_equipment(client, name="Bike", category="Land", total_units=4)

    response = client.get("/equipment")
    assert response.status_code == 200
    items = response.get_json()
    assert len(items) == 1

    item = items[0]
    assert item["id"] == created["id"]
    assert item["name"] == "Bike"
    assert item["category"] == "Land"
    assert item["total_units"] == 4
    assert item["available_units"] == 4

# Feature - View/List Equipment
def test_list_equipment_includes_all_items_without_login(client):
    """Customers can list every equipment record without authenticating."""
    first = _create_equipment(client, name="Helmet", category="Safety", total_units=10)
    second = _create_equipment(client, name="Paddle", category="Water", total_units=5)

    response = client.get("/equipment")
    assert response.status_code == 200
    items = response.get_json()
    ids = {item["id"] for item in items}
    names = {item["name"] for item in items}

    assert first["id"] in ids
    assert second["id"] in ids
    assert names == {"Helmet", "Paddle"}
    assert len(items) == 2

# Feature - View/List Equipment
def test_list_equipment_exposes_required_rental_status(client):
    """Listed equipment must include a rental status from allowed set."""
    _create_equipment(client, name="Canoe", category="Water", total_units=1)

    response = client.get("/equipment")
    assert response.status_code == 200
    items = response.get_json()
    assert len(items) == 1

    item = items[0]
    assert "status" in item, (
        "Requires a rental status (Available, Rented, On-Hold, Overdue); "
        f"response keys were: {sorted(item.keys())}"
    )
    assert item["status"] in VALID_RENTAL_STATUSES

# Feature - View one equipment record
def test_get_equipment_returns_persisted_record(client):
    """GET /equipment/<id> returns the same fields stored at create time."""
    created = _create_equipment(client, name="Tent", category="Camping", total_units=3)
    equipment_id = created["id"]

    response = client.get(f"/equipment/{equipment_id}")
    assert response.status_code == 200
    data = response.get_json()

    assert data["id"] == equipment_id
    assert data["name"] == "Tent"
    assert data["category"] == "Camping"
    assert data["total_units"] == 3
    assert data["available_units"] == 3

# Feature - View one equipment record
def test_get_equipment_exposes_required_rental_status(client):
    """A single equipment record must show rental status without login."""
    created = _create_equipment(client, name="Snowboard", category="Snow", total_units=1)

    response = client.get(f"/equipment/{created['id']}")
    assert response.status_code == 200
    data = response.get_json()

    assert "status" in data, (
        "Requires viewing equipment status without logging in; "
        f"response keys were: {sorted(data.keys())}"
    )
    assert data["status"] in VALID_RENTAL_STATUSES

# Feature - View one equipment record
def test_get_equipment_nonexistent_id_returns_404(client):
    """Requesting an unknown equipment ID must not invent a record."""
    response = client.get("/equipment/9999")
    assert response.status_code == 404
    body = response.get_json()
    assert "error" in body
    assert "not found" in body["error"].lower()

# Feature - Add Equipment
def test_add_equipment_stores_price_and_description(client):
    """New equipment records must store price and description."""
    response = client.post(
        "/equipment",
        json={
            "name": "Kayak",
            "category": "Water",
            "total_units": 2,
            "price": 45.00,
            "description": "Single-seat recreational kayak",
        },
    )
    assert response.status_code == 201
    created = response.get_json()
    assert "price" in created, (
        "Requires price on equipment records; "
        f"response keys were: {sorted(created.keys())}"
    )
    assert "description" in created, (
        "Requires description on equipment records; "
        f"response keys were: {sorted(created.keys())}"
    )
    assert created["price"] == 45.00
    assert created["description"] == "Single-seat recreational kayak"

    get_resp = client.get(f"/equipment/{created['id']}")
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert data["price"] == 45.00
    assert data["description"] == "Single-seat recreational kayak"

# Feature - Add Equipment
def test_add_equipment_via_form_persists_record(client):
    """Form UI can add equipment and persist it for later lookup."""
    response = client.post(
        "/ui/equipment",
        data={"name": "Canoe", "category": "Water", "total_units": "2"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    items = client.get("/equipment").get_json()
    assert len(items) == 1
    assert items[0]["name"] == "Canoe"
    assert items[0]["category"] == "Water"
    assert items[0]["total_units"] == 2
    assert items[0]["available_units"] == 2

# Feature - Edit Equipment
def test_edit_equipment_updates_price_and_description(client):
    """Editing equipment must update price and description in storage."""
    created = _create_equipment(client, name="Tent", category="Camping", total_units=1)
    equipment_id = created["id"]

    update_resp = client.put(
        f"/equipment/{equipment_id}",
        json={"price": 30.00, "description": "4-person dome tent"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.get_json()
    assert "price" in updated, (
        "Requires editable price; "
        f"response keys were: {sorted(updated.keys())}"
    )
    assert "description" in updated, (
        "Requires editable description; "
        f"response keys were: {sorted(updated.keys())}"
    )
    assert updated["price"] == 30.00
    assert updated["description"] == "4-person dome tent"

    get_resp = client.get(f"/equipment/{equipment_id}")
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert data["price"] == 30.00
    assert data["description"] == "4-person dome tent"

# Feature - Edit Equipment
def test_edit_equipment_nonexistent_id_returns_404(client):
    """Editing an unknown equipment ID must not invent a record."""
    response = client.put(
        "/equipment/9999",
        json={"name": "Ghost Item", "category": "None"},
    )
    assert response.status_code == 404
    body = response.get_json()
    assert "error" in body
    assert "not found" in body["error"].lower()
    assert client.get("/equipment").get_json() == []

# Feature - Edit Equipment
def test_edit_equipment_via_form_updates_record(client):
    """Form UI can edit equipment fields and persist the changes."""
    created = _create_equipment(client, name="Old Name", category="Misc", total_units=1)
    equipment_id = created["id"]

    response = client.post(
        f"/ui/equipment/{equipment_id}/edit",
        data={
            "name": "New Name",
            "category": "Updated",
            "total_units": "4",
            "price": "25.00",
            "description": "Updated gear",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    get_resp = client.get(f"/equipment/{equipment_id}")
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert data["name"] == "New Name"
    assert data["category"] == "Updated"
    assert data["total_units"] == 4

# Feature - Delete Equipment
def test_delete_equipment_nonexistent_id_returns_404(client):
    """Deleting an unknown equipment ID must report not found."""
    response = client.delete("/equipment/9999")
    assert response.status_code == 404
    body = response.get_json()
    assert "error" in body
    assert "not found" in body["error"].lower()

# Feature - Delete Equipment
def test_delete_equipment_via_form_removes_record(client):
    """Form UI can remove equipment from subsequent lookups."""
    created = _create_equipment(client, name="Skis", category="Snow", total_units=2)
    equipment_id = created["id"]

    response = client.post(
        f"/ui/equipment/{equipment_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert client.get(f"/equipment/{equipment_id}").status_code == 404
    assert client.get("/equipment").get_json() == []

# Feature - Set Equipment Availability/Status
def test_set_equipment_unavailable_persists(client):
    """Marking equipment unavailable is stored and visible on later GET."""
    created = _create_equipment(client, name="Bike", category="Land", total_units=2)
    equipment_id = created["id"]

    patch_resp = client.patch(
        f"/equipment/{equipment_id}/status",
        json={"is_available": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["is_available"] is False

    get_resp = client.get(f"/equipment/{equipment_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["is_available"] is False

# Feature - Set Equipment Availability/Status
def test_set_equipment_out_of_service_stores_reason(client):
    """Out-of-service equipment must store a short reason."""
    created = _create_equipment(client, name="Kayak", category="Water", total_units=1)
    equipment_id = created["id"]

    response = client.patch(
        f"/equipment/{equipment_id}/status",
        json={"is_available": False, "reason": "Hull crack under repair"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "reason" in data, (
        "Requires an out-of-service reason; "
        f"response keys were: {sorted(data.keys())}"
    )
    assert data["reason"] == "Hull crack under repair"

    get_resp = client.get(f"/equipment/{equipment_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["reason"] == "Hull crack under repair"

# Feature - Set Equipment Availability/Status
def test_set_equipment_out_of_service_blocks_checkout(client):
    """Out-of-service equipment must be removed from the rentable pool."""
    created = _create_equipment(client, name="Helmet", category="Safety", total_units=1)
    equipment_id = created["id"]
    renter = client.post(
        "/renters",
        json={"name": "Alex", "email": "alex@example.com"},
    ).get_json()

    patch_resp = client.patch(
        f"/equipment/{equipment_id}/status",
        json={"is_available": False, "reason": "Safety recall"},
    )
    assert patch_resp.status_code == 200

    checkout_resp = client.post(
        "/rentals",
        json={"equipment_id": equipment_id, "renter_id": renter["id"]},
    )
    assert checkout_resp.status_code in (400, 409)
    assert client.get("/rentals").get_json() == []
    assert client.get(f"/equipment/{equipment_id}").get_json()["available_units"] == 1

# Feature - Set Equipment Availability/Status
def test_set_equipment_status_nonexistent_id_returns_404(client):
    """Setting status on an unknown equipment ID must report not found."""
    response = client.patch(
        "/equipment/9999/status",
        json={"is_available": False},
    )
    assert response.status_code == 404
    body = response.get_json()
    assert "error" in body
    assert "not found" in body["error"].lower()

# Feature - Check Equipment Availability
def test_check_availability_reflects_out_of_service(client):
    """Availability must show equipment as unavailable after out-of-service."""
    created = _create_equipment(client, name="Skis", category="Snow", total_units=2)
    equipment_id = created["id"]

    client.patch(
        f"/equipment/{equipment_id}/status",
        json={"is_available": False, "reason": "Binding broken"},
    )

    response = client.get(f"/equipment/{equipment_id}/availability")
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_available"] is False

# Feature - Check Equipment Availability
def test_check_availability_exposes_required_rental_status(client):
    """Availability must include a rental status from the allowed set."""
    created = _create_equipment(client, name="Snowboard", category="Snow", total_units=1)

    response = client.get(f"/equipment/{created['id']}/availability")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data, (
        "Requires a rental status (Available, Rented, On-Hold, Overdue); "
        f"response keys were: {sorted(data.keys())}"
    )
    assert data["status"] in VALID_RENTAL_STATUSES

# Feature - Check Equipment Availability
def test_check_availability_updates_after_checkout(client):
    """Available units decrease after a successful rental checkout."""
    created = _create_equipment(client, name="Ladder", category="Climbing", total_units=3)
    equipment_id = created["id"]
    renter = client.post(
        "/renters",
        json={"name": "Sam", "email": "sam@example.com"},
    ).get_json()

    checkout_resp = client.post(
        "/rentals",
        json={"equipment_id": equipment_id, "renter_id": renter["id"]},
    )
    assert checkout_resp.status_code == 201

    response = client.get(f"/equipment/{equipment_id}/availability")
    assert response.status_code == 200
    data = response.get_json()
    assert data["available_units"] == 2
    assert data["total_units"] == 3

# Feature - Check Equipment Availability
def test_check_availability_nonexistent_id_returns_404(client):
    """Checking availability for an unknown ID must report not found."""
    response = client.get("/equipment/9999/availability")
    assert response.status_code == 404
    body = response.get_json()
    assert "error" in body
    assert "not found" in body["error"].lower()

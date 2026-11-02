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

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

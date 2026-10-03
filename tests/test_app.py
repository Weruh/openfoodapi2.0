import json
from unittest.mock import patch

import pytest

from app import create_app
from openfoodfacts import ExternalAPIError, ProductNotFound


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_read_routes(client):
    assert client.get("/").status_code == 200
    response = client.get("/inventory")
    assert response.status_code == 200
    assert len(response.json) == 2
    assert client.get("/inventory/1").json["product_name"] == "Organic Almond Milk"


def test_crud_lifecycle(client):
    response = client.post("/inventory", json={"product_name": "Bread", "price": 50, "stock": 4})
    assert response.status_code == 201
    item_id = response.json["id"]
    assert client.get(f"/inventory/{item_id}").json["stock"] == 4
    response = client.patch(f"/inventory/{item_id}", json={"price": 60, "stock": 0})
    assert response.status_code == 200
    assert response.json["price"] == 60
    assert response.json["stock"] == 0
    assert response.json["product_name"] == "Bread"
    assert client.delete(f"/inventory/{item_id}").status_code == 204
    assert client.get(f"/inventory/{item_id}").status_code == 404

    new = client.post("/inventory", json={"product_name": "Rice", "price": 20, "stock": 1})
    assert new.json["id"] > item_id


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_inventory_item(client, method):
    response = getattr(client, method)("/inventory/999")
    assert response.status_code == 404
    assert "error" in response.json


@pytest.mark.parametrize("data", [
    {}, [], None, {"product_name": "Rice"},
    {"product_name": " ", "price": 20, "stock": 1},
    {"product_name": "Rice", "price": -1, "stock": 1},
    {"product_name": "Rice", "price": True, "stock": 1},
    {"product_name": "Rice", "price": "20", "stock": 1},
    {"product_name": "Rice", "price": 20, "stock": 1.5},
    {"product_name": "Rice", "price": 20, "stock": False},
    {"product_name": "Rice", "price": 20, "stock": -1},
    {"product_name": "Rice", "price": 20, "stock": 1, "id": 99},
])
def test_invalid_create_does_not_change_inventory(client, data):
    response = client.post("/inventory", data=json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    assert len(client.get("/inventory").json) == 2


@pytest.mark.parametrize("data", [{}, {"id": 10}, {"price": -1}, {"stock": 2.5}, {"brands": 3}, {"barcode": "abc"}, {"price": float("inf")}])
def test_invalid_patch_is_atomic(client, data):
    before = client.get("/inventory/1").json
    assert client.patch("/inventory/1", json=data).status_code == 400
    assert client.get("/inventory/1").json == before


def test_bad_json_and_content_type(client):
    assert client.post("/inventory", data="{", content_type="application/json").status_code == 400
    assert client.post("/inventory", data="hello").status_code == 415


def test_lookup_routes(client):
    product = {"product_name": "Milk", "barcode": "123", "brands": "Brand", "ingredients_text": "Milk"}
    with patch("app.find_by_barcode", return_value=product) as lookup:
        response = client.get("/products/barcode/123")
        assert response.json == product
        lookup.assert_called_once_with("123")
    with patch("app.find_by_name", return_value=[product]) as lookup:
        assert client.get("/products/search?name=milk").json == [product]
        lookup.assert_called_once_with("milk")
    assert len(client.get("/inventory").json) == 2
    assert client.get("/products/search").status_code == 400
    assert client.get("/products/barcode/abc").status_code == 400
    with patch("app.find_by_name", return_value=[]):
        assert client.get("/products/search?name=missing").json == []


@pytest.mark.parametrize("error,status", [(ProductNotFound("Missing"), 404), (ExternalAPIError("Unavailable"), 502)])
def test_external_route_errors(client, error, status):
    with patch("app.find_by_barcode", side_effect=error):
        response = client.get("/products/barcode/123")
        assert response.status_code == status
        assert "error" in response.json


def test_separate_apps_have_separate_inventory(client):
    client.delete("/inventory/1")
    assert len(create_app().test_client().get("/inventory").json) == 2

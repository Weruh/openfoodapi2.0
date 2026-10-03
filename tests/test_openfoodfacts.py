from unittest.mock import Mock, patch

import pytest
import requests

from openfoodfacts import ExternalAPIError, ProductNotFound, find_by_barcode, find_by_name


def fake_response(data, status=200):
    response = Mock(status_code=status)
    response.json.return_value = data
    return response


def test_barcode_lookup():
    response = fake_response({"status": "success", "product": {"product_name": "Milk", "brands": "Brand"}})
    with patch("openfoodfacts.requests.get", return_value=response) as get:
        product = find_by_barcode("00123")
        assert product == {"product_name": "Milk", "brands": "Brand", "ingredients_text": "", "barcode": "00123"}
        assert get.call_args.args[0].endswith("/api/v3/product/00123.json")
        assert get.call_args.kwargs["timeout"] == 10
        assert "User-Agent" in get.call_args.kwargs["headers"]


@pytest.mark.parametrize("data,status", [({"status": 0}, 200), ({}, 404)])
def test_missing_product(data, status):
    with patch("openfoodfacts.requests.get", return_value=fake_response(data, status)):
        with pytest.raises(ProductNotFound):
            find_by_barcode("123")


def test_search_and_empty_results():
    with patch("openfoodfacts.requests.get", return_value=fake_response({"products": [{"code": "123", "product_name": "Oats"}]})) as get:
        assert find_by_name("oats")[0]["product_name"] == "Oats"
        assert get.call_args.kwargs["params"]["search_terms"] == "oats"
    with patch("openfoodfacts.requests.get", return_value=fake_response({"products": []})):
        assert find_by_name("missing") == []


@pytest.mark.parametrize("error", [requests.Timeout(), requests.ConnectionError()])
def test_network_errors(error):
    with patch("openfoodfacts.requests.get", side_effect=error):
        with pytest.raises(ExternalAPIError):
            find_by_barcode("123")


def test_http_error():
    response = fake_response({})
    response.raise_for_status.side_effect = requests.HTTPError("503")
    with patch("openfoodfacts.requests.get", return_value=response):
        with pytest.raises(ExternalAPIError):
            find_by_name("oats")


def test_invalid_json():
    response = fake_response({})
    response.json.side_effect = ValueError("Invalid JSON")
    with patch("openfoodfacts.requests.get", return_value=response):
        with pytest.raises(ExternalAPIError):
            find_by_barcode("123")


@pytest.mark.parametrize("data", [[], {"products": None}, {"products": ["invalid"]}])
def test_invalid_search_shape(data):
    with patch("openfoodfacts.requests.get", return_value=fake_response(data)):
        with pytest.raises(ExternalAPIError):
            find_by_name("oats")

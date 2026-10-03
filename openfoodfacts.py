import os

import requests

BASE_URL = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": os.getenv("OFF_USER_AGENT", "InventoryLearningApp/1.0")}
FIELDS = "code,product_name,brands,ingredients_text"


class ProductNotFound(Exception):
    pass


class ExternalAPIError(Exception):
    pass


def get_json(url, params=None):
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 404:
            raise ProductNotFound("Product not found.")
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data
    except (requests.RequestException, ValueError) as error:
        raise ExternalAPIError("Open Food Facts is unavailable or returned invalid data.") from error


def product_details(product):
    return {
        "barcode": str(product.get("code") or ""),
        "product_name": product.get("product_name") or "Unnamed product",
        "brands": product.get("brands") or "",
        "ingredients_text": product.get("ingredients_text") or "",
    }


def find_by_barcode(barcode):
    data = get_json(f"{BASE_URL}/api/v3/product/{barcode}.json", {"fields": FIELDS})
    product = data.get("product")
    if not isinstance(product, dict) or not product:
        raise ProductNotFound("Product not found.")
    details = product_details(product)
    details["barcode"] = barcode
    return details


def find_by_name(name):

    data = get_json(f"{BASE_URL}/cgi/search.pl", {
        "search_terms": name, "search_simple": 1, "action": "process",
        "json": 1, "page_size": 5, "fields": FIELDS,
    })
    products = data.get("products")
    if not isinstance(products, list):
        raise ExternalAPIError("Open Food Facts returned invalid search data.")

    results = []
    for product in products:
        if not isinstance(product, dict):
            raise ExternalAPIError("Open Food Facts returned invalid search data.")
        results.append(product_details(product))
    return results

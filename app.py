from copy import deepcopy
import math
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from openfoodfacts import ExternalAPIError, ProductNotFound, find_by_barcode, find_by_name

SAMPLE_ITEMS = [
    {"id": 1, "product_name": "Organic Almond Milk", "brands": "Silk",
     "ingredients_text": "Filtered water, almonds, cane sugar", "barcode": "",
     "price": 250.0, "stock": 10},
    {"id": 2, "product_name": "Oatmeal", "brands": "Sample Brand",
     "ingredients_text": "Whole grain oats", "barcode": "", "price": 150.0, "stock": 20},
]


def validate_item(data, partial=False):
    if not isinstance(data, dict) or not data:
        return "Send a non-empty JSON object."
    allowed = ["product_name", "brands", "ingredients_text", "barcode", "price", "stock"]
    for field in data:
        if field not in allowed:
            return f"Unknown field: {field}"


    if not partial:
        for field in ["product_name", "price", "stock"]:
            if field not in data:
                return f"{field} is required."
    for field in ("product_name", "brands", "ingredients_text", "barcode"):
        if field in data and not isinstance(data[field], str):
            return f"{field} must be text."
    if "product_name" in data and not data["product_name"].strip():
        return "product_name cannot be empty."
    if "barcode" in data:
        barcode = data["barcode"]
        if barcode != "":
            if not barcode.isascii() or not barcode.isdigit():
                return "barcode must contain digits only, or be empty."
    if "price" in data:
        price = data["price"]
        if type(price) not in (int, float):
            return "price must be a number."
        if price < 0 or not math.isfinite(price):
            return "price must be a finite, non-negative number."
    if "stock" in data:
        stock = data["stock"]
        if type(stock) is not int:
            return "stock must be a whole number."
        if stock < 0:
            return "stock cannot be negative."
    return None


def create_app():
    app = Flask(__name__)

    inventory = deepcopy(SAMPLE_ITEMS)
    next_id = 3

    def find_item(item_id):

        for item in inventory:
            if item["id"] == item_id:
                return item
        return None

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(ProductNotFound)
    def product_missing(error):
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(ExternalAPIError)
    def external_error(error):
        return jsonify({"error": str(error)}), 502

    @app.get("/")
    def home():
        return jsonify({"message": "Inventory API", "inventory": "/inventory", "interface": "python cli.py"})

    @app.get("/inventory")
    def get_inventory():
        return jsonify(inventory)

    @app.get("/inventory/<int:item_id>")
    def get_item(item_id):
        item = find_item(item_id)
        if item is None:
            return jsonify({"error": "Item not found."}), 404
        return jsonify(item)

    @app.post("/inventory")
    def add_item():
        nonlocal next_id
        data = request.get_json()
        error = validate_item(data)
        if error:
            return jsonify({"error": error}), 400
        item = {
            "id": next_id,
            "product_name": data["product_name"],
            "price": data["price"],
            "stock": data["stock"],
            "brands": data.get("brands", ""),
            "ingredients_text": data.get("ingredients_text", ""),
            "barcode": data.get("barcode", ""),
        }
        inventory.append(item)
        next_id += 1
        return jsonify(item), 201

    @app.patch("/inventory/<int:item_id>")
    def update_item(item_id):
        item = find_item(item_id)
        if item is None:
            return jsonify({"error": "Item not found."}), 404
        data = request.get_json()
        error = validate_item(data, partial=True)
        if error:
            return jsonify({"error": error}), 400

        for field in data:
            item[field] = data[field]
        return jsonify(item)

    @app.delete("/inventory/<int:item_id>")
    def delete_item(item_id):
        item = find_item(item_id)
        if item is None:
            return jsonify({"error": "Item not found."}), 404
        inventory.remove(item)
        return "", 204

    @app.get("/products/barcode/<barcode>")
    def barcode_lookup(barcode):
        if not (barcode.isascii() and barcode.isdigit()):
            return jsonify({"error": "Barcode must contain digits only."}), 400
        return jsonify(find_by_barcode(barcode))

    @app.get("/products/search")
    def name_lookup():
        name = request.args.get("name", "").strip()
        if not name:
            return jsonify({"error": "The name query parameter is required."}), 400
        return jsonify(find_by_name(name))

    return app


app = create_app()


if __name__ == "__main__":
    app.run()

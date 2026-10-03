# Simple Inventory Management System

A beginner-friendly Python assignment: a Flask REST API, an inventory stored in a Python list, a command-line interface (CLI), and tests. Employees can add, view, update, and delete items, search Open Food Facts, and import product details into inventory.

The CLI is the administrator interface for this project. No browser frontend is needed to use it.

## 1. Setup

Use Python 3.10 or newer. In the project folder, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate` instead.

## 2. Start the API

In your first terminal (with the virtual environment activated):

```bash
python app.py
```

The API runs at `http://127.0.0.1:5000`. Keep this terminal open.

To use Flask Debug Mode locally instead:

```bash
flask --app app run --debug
```

## 3. Use the CLI

Open a second terminal in the same folder and activate the virtual environment again.

```bash
python cli.py
```

You will see this menu:

```text
1. View all items
2. View one item
3. Add an item
4. Update an item
5. Delete an item
6. Find a product by barcode
7. Find products by name
8. Import a product into inventory
0. Exit
```

Type a number and press Enter. The program asks you for the details it needs.

For example, to add bread, choose **3**. Enter `Bread` for the name, `50` for the price, and `10` for the stock. To see it, choose **1**.

To update an item, choose **4** and enter its ID. Press Enter at any field you want to keep. To delete an item, choose **5** and enter its ID.

Choices **6** and **7** only find products. Choice **8** finds a barcode, asks for your store's price and stock, and saves the product to inventory. You can search by name with **7**, then use a result's barcode with **8**. Try barcode `3017624010701`.

Price is a number in your store's currency (for example KES). Stock is a whole number. Neither can be negative. An ID is a number the server gives each item so we can find it later.

If you use a different server port, change `API_URL` near the top of `cli.py`.

## 4. Route plan

| Method and route | Input | Output | Data change / CLI trigger |
| --- | --- | --- | --- |
| GET `/` | None | API information, 200 | None; browser or Postman |
| GET `/inventory` | None | List of items, 200 | None; menu 1 |
| GET `/inventory/<id>` | Inventory ID | Item, 200 | None; menu 2 |
| POST `/inventory` | JSON item | Created item, 201 | Append to list; menu 3 or 8 |
| PATCH `/inventory/<id>` | ID and JSON fields to change | Updated item, 200 | Change selected fields; menu 4 |
| DELETE `/inventory/<id>` | Inventory ID | Empty response, 204 | Remove item; menu 5 |
| GET `/products/barcode/<barcode>` | Barcode digits | External product details, 200 | None; menu 6 or first step of menu 8 |
| GET `/products/search?name=milk` | Product name | Up to five external results, 200 | None; menu 7 |

Errors return JSON such as `{"error": "Item not found."}`. Invalid input returns 400, missing items or barcodes return 404, an unsupported request content type returns 415, and external service failures return 502. An empty name search result returns `[]` with 200.

### Inventory data

The sample list is in `app.py`. These are illustrative mock products, not fetched product records. Each item has an ID:

```json
{
  "id": 1,
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "ingredients_text": "Filtered water, almonds, cane sugar",
  "barcode": "",
  "price": 250.0,
  "stock": 10
}
```

For POST, `product_name`, `price`, and `stock` are required. `brands`, `ingredients_text`, and `barcode` are optional strings. PATCH accepts any of these fields, but requires at least one. The ID cannot be changed. Barcodes are strings to preserve leading zeroes.

### Try a route with curl or Postman

```bash
curl http://127.0.0.1:5000/inventory
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name":"Rice","price":180,"stock":12}'
curl -X PATCH http://127.0.0.1:5000/inventory/1 \
  -H "Content-Type: application/json" -d '{"stock":7}'
curl -X DELETE http://127.0.0.1:5000/inventory/1
```

In Postman, select the method, enter the URL, and use **Body → raw → JSON** for POST and PATCH.

## 5. How the code works

- `app.py`: Flask routes, validation, sample inventory, and list changes. `create_app()` creates a fresh list for each app instance.
- `openfoodfacts.py`: Fetches external JSON, handles failures, and extracts product name, brand, ingredients, and barcode.
- `cli.py`: Shows a numbered menu, reads answers with `input()`, and uses `requests` to call Flask.
- `tests/`: Tests API routes, CLI commands, and external API interactions using pytest and `unittest.mock`.
- `requirements.txt`: Lists the Python packages needed.

The request flow is:

```text
Employee menu choice -> CLI HTTP request -> Flask route -> Python inventory list
                                            |
                                            +-> Open Food Facts (lookup routes)
```

`POST` appends a dictionary to the list. `GET` reads it. `PATCH` uses a loop to change only the supplied fields. `DELETE` removes it. The next ID increases on each successful add, even after deleting an item.

## 6. Run tests

```bash
python -m pytest -q
```

Tests use Flask's test client and mocked HTTP responses. They do not need a running server or internet access. They check CRUD, validation, missing items, barcode and name lookup, CLI commands, importing, and external failures.

## 7. Open Food Facts integration

Barcode lookups use `/api/v3/product/<barcode>.json`. Name searches use `/cgi/search.pl` with query parameters. See the [official API documentation](https://openfoodfacts.github.io/openfoodfacts-server/api/) and [search documentation](https://openfoodfacts.github.io/openfoodfacts-server/api/#search).

The integration sends a custom User-Agent and uses a 10-second timeout. Before using live lookups, identify your app with your contact email:

```bash
export OFF_USER_AGENT="InventoryLearningApp/1.0 (your-email@example.com)"
python app.py
```

Live lookups require internet access. Product details may be incomplete; missing brand and ingredients become empty strings. Stock and price belong to your store and are entered by you. Data is provided by [Open Food Facts](https://world.openfoodfacts.org/) under the [Open Database License](https://opendatacommons.org/licenses/odbl/).

## 8. Assignment scope

Storage is temporary: restarting the server restores the two sample items. Use one Flask process for this exercise. This is a local learning project with no authentication or permanent database.

No commits or pushes were made. Git branches, pull requests, and GitHub submission remain for you to handle when ready; this implementation does not complete the rubric's Git management workflow.

## 9. A few Python words explained

- A **list**, like `inventory`, holds several items together.
- A **dictionary**, like one item, stores labeled values such as `"price": 50`.
- A **function**, written with `def`, is a named set of steps we can run again.
- A **for loop** repeats steps for each item in a list.
- An **if** chooses what to do when something is true.
- `return` sends an answer back from a function.
- `input()` asks the person using the program a question.
- `try` and `except` let us show an error and keep the menu running.
- An **API** lets one program ask another program for information.
- **JSON** is the text format our CLI and Flask use to send dictionaries and lists.

Start reading `cli.py` at `main()`: it prints the menu, reads a choice, and runs the matching function. Then read `view_all_items()` and `add_item()`. In `app.py`, read `get_inventory()` and `add_item()` to see what Flask does with those requests.

The `@app.get(...)` line tells Flask which URL runs a function. `create_app()` groups the server setup in one place so each test can start with fresh inventory. `nonlocal next_id` lets `add_item()` change the ID counter defined inside `create_app()`.

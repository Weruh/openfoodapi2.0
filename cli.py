import json

import requests

API_URL = "http://127.0.0.1:5000"


def send_request(method, path, data=None, params=None):
    response = requests.request(
        method,
        API_URL + path,
        json=data,
        params=params,
        timeout=15,
    )


    if response.status_code == 204:
        return {"message": "Item deleted."}

    answer = response.json()
    if not response.ok:
        raise ValueError(answer.get("error", "The request failed."))

    return answer


def show(answer):
    print(json.dumps(answer, indent=2))


def ask_for_price_and_stock():

    price = float(input("Price: "))
    stock = int(input("Stock: "))
    return {"price": price, "stock": stock}


def view_all_items():
    answer = send_request("GET", "/inventory")
    show(answer)


def view_one_item():
    item_id = int(input("Item ID: "))
    answer = send_request("GET", f"/inventory/{item_id}")
    show(answer)


def add_item():
    name = input("Product name: ").strip()
    item = ask_for_price_and_stock()
    item["product_name"] = name
    answer = send_request("POST", "/inventory", data=item)
    show(answer)


def update_item():
    item_id = int(input("Item ID: "))
    changes = {}


    name = input("New name (Enter to keep): ").strip()
    price = input("New price (Enter to keep): ").strip()
    stock = input("New stock (Enter to keep): ").strip()

    if name != "":
        changes["product_name"] = name
    if price != "":
        changes["price"] = float(price)
    if stock != "":
        changes["stock"] = int(stock)

    if changes == {}:
        print("No changes entered.")
        return

    answer = send_request("PATCH", f"/inventory/{item_id}", data=changes)
    show(answer)


def delete_item():
    item_id = int(input("Item ID: "))
    answer = send_request("DELETE", f"/inventory/{item_id}")
    show(answer)


def ask_for_barcode():
    barcode = input("Barcode: ").strip()
    if not barcode.isascii() or not barcode.isdigit():
        raise ValueError("A barcode must contain digits only.")
    return barcode


def find_by_barcode():
    barcode = ask_for_barcode()
    answer = send_request("GET", f"/products/barcode/{barcode}")
    show(answer)


def find_by_name():
    name = input("Product name to search for: ").strip()
    answer = send_request("GET", "/products/search", params={"name": name})
    show(answer)


def import_product():

    barcode = ask_for_barcode()
    product = send_request("GET", f"/products/barcode/{barcode}")
    show(product)


    store_details = ask_for_price_and_stock()
    product["price"] = store_details["price"]
    product["stock"] = store_details["stock"]


    answer = send_request("POST", "/inventory", data=product)
    show(answer)


def main():
    while True:
        print("\nINVENTORY MENU")
        print("1. View all items")
        print("2. View one item")
        print("3. Add an item")
        print("4. Update an item")
        print("5. Delete an item")
        print("6. Find a product by barcode")
        print("7. Find products by name")
        print("8. Import a product into inventory")
        print("0. Exit")

        try:
            choice = input("Choose a number: ").strip()

            if choice == "0":
                print("Goodbye!")
                break
            elif choice == "1":
                view_all_items()
            elif choice == "2":
                view_one_item()
            elif choice == "3":
                add_item()
            elif choice == "4":
                update_item()
            elif choice == "5":
                delete_item()
            elif choice == "6":
                find_by_barcode()
            elif choice == "7":
                find_by_name()
            elif choice == "8":
                import_product()
            else:
                print("Please choose a number from 0 to 8.")
        except requests.RequestException:
            print("Cannot reach the API. Check that app.py is running and try again.")
        except ValueError as error:
            print(f"Error: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()

from unittest.mock import Mock, patch

import requests

import cli


def test_view_all_items():
    with patch("cli.send_request", return_value=[]) as request:
        cli.view_all_items()
        request.assert_called_once_with("GET", "/inventory")


def test_view_one_item():
    with patch("builtins.input", return_value="1"):
        with patch("cli.send_request", return_value={"id": 1}) as request:
            cli.view_one_item()
            request.assert_called_once_with("GET", "/inventory/1")


def test_add_item():

    with patch("builtins.input", side_effect=["Bread", "50", "10"]):
        with patch("cli.send_request", return_value={"id": 3}) as request:
            cli.add_item()
            request.assert_called_once_with(
                "POST", "/inventory",
                data={"product_name": "Bread", "price": 50.0, "stock": 10},
            )


def test_update_item():
    with patch("builtins.input", side_effect=["1", "Milk", "0", "0"]):
        with patch("cli.send_request", return_value={"id": 1}) as request:
            cli.update_item()
            request.assert_called_once_with(
                "PATCH", "/inventory/1",
                data={"product_name": "Milk", "price": 0.0, "stock": 0},
            )


def test_update_keeps_blank_fields():
    with patch("builtins.input", side_effect=["1", "", "", "5"]):
        with patch("cli.send_request", return_value={"id": 1}) as request:
            cli.update_item()
            request.assert_called_once_with("PATCH", "/inventory/1", data={"stock": 5})


def test_update_without_changes(capsys):
    with patch("builtins.input", side_effect=["1", "", "", ""]):
        with patch("cli.send_request") as request:
            cli.update_item()
            request.assert_not_called()
    assert "No changes" in capsys.readouterr().out


def test_delete_item():
    with patch("builtins.input", return_value="1"):
        with patch("cli.send_request", return_value={"message": "Item deleted."}) as request:
            cli.delete_item()
            request.assert_called_once_with("DELETE", "/inventory/1")


def test_find_by_barcode():
    with patch("builtins.input", return_value="00123"):
        with patch("cli.send_request", return_value={"product_name": "Milk"}) as request:
            cli.find_by_barcode()
            request.assert_called_once_with("GET", "/products/barcode/00123")


def test_find_by_name():
    with patch("builtins.input", return_value="oat milk"):
        with patch("cli.send_request", return_value=[]) as request:
            cli.find_by_name()
            request.assert_called_once_with("GET", "/products/search", params={"name": "oat milk"})


def test_import_product():
    product = {"product_name": "Milk", "barcode": "123"}
    with patch("builtins.input", side_effect=["123", "30", "2"]):
        with patch("cli.send_request", side_effect=[product, {"id": 3}]) as request:
            cli.import_product()
            assert request.call_count == 2
            assert request.call_args_list[0].args == ("GET", "/products/barcode/123")
            request.assert_called_with(
                "POST", "/inventory",
                data={"product_name": "Milk", "barcode": "123", "price": 30.0, "stock": 2},
            )


def test_failed_import_does_not_save():
    with patch("builtins.input", side_effect=["8", "123", "0"]):
        with patch("cli.send_request", side_effect=ValueError("Product not found")) as request:
            cli.main()
            assert request.call_count == 1


def test_menu_exit(capsys):
    with patch("builtins.input", return_value="0"):
        cli.main()
    assert "Goodbye!" in capsys.readouterr().out


def test_menu_dispatches_all_choices():
    function_names = [
        "view_all_items", "view_one_item", "add_item", "update_item",
        "delete_item", "find_by_barcode", "find_by_name", "import_product",
    ]
    for number, function_name in enumerate(function_names, start=1):
        with patch("builtins.input", side_effect=[str(number), "0"]):
            with patch("cli." + function_name) as action:
                cli.main()
                action.assert_called_once()


def test_invalid_menu_choice(capsys):
    with patch("builtins.input", side_effect=["9", "0"]):
        cli.main()
    assert "Please choose" in capsys.readouterr().out


def test_invalid_number_keeps_menu_open(capsys):
    with patch("builtins.input", side_effect=["3", "Bread", "abc", "0"]):
        with patch("cli.send_request") as request:
            cli.main()
            request.assert_not_called()
    assert "Error:" in capsys.readouterr().out


def test_invalid_barcode_does_not_send_request(capsys):
    with patch("builtins.input", side_effect=["6", "../inventory", "0"]):
        with patch("cli.send_request") as request:
            cli.main()
            request.assert_not_called()
    assert "digits only" in capsys.readouterr().out


def test_network_failure_keeps_menu_open(capsys):
    with patch("builtins.input", side_effect=["1", "0"]):
        with patch("cli.send_request", side_effect=requests.ConnectionError()):
            cli.main()
    assert "Cannot reach" in capsys.readouterr().out


def test_send_request():
    response = Mock(status_code=200, ok=True)
    response.json.return_value = [{"id": 1}]
    with patch("cli.requests.request", return_value=response) as request:
        assert cli.send_request("GET", "/inventory") == [{"id": 1}]
        request.assert_called_once_with(
            "GET", "http://127.0.0.1:5000/inventory", json=None, params=None, timeout=15,
        )


def test_send_request_delete():
    response = Mock(status_code=204)
    with patch("cli.requests.request", return_value=response):
        assert cli.send_request("DELETE", "/inventory/1") == {"message": "Item deleted."}
        response.json.assert_not_called()


def test_api_error_keeps_menu_open(capsys):
    response = Mock(status_code=404, ok=False)
    response.json.return_value = {"error": "Item not found."}
    with patch("builtins.input", side_effect=["2", "999", "0"]):
        with patch("cli.requests.request", return_value=response):
            cli.main()
    assert "Item not found" in capsys.readouterr().out


def test_invalid_json_keeps_menu_open(capsys):
    response = Mock(status_code=200)
    response.json.side_effect = ValueError("Invalid JSON")
    with patch("builtins.input", side_effect=["1", "0"]):
        with patch("cli.requests.request", return_value=response):
            cli.main()
    assert "Error:" in capsys.readouterr().out


def test_keyboard_interrupt_exits(capsys):
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        cli.main()
    assert "Goodbye!" in capsys.readouterr().out

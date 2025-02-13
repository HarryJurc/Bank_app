import datetime
from datetime import datetime
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.utils import (get_exchange_rates, get_greeting, get_operations_data, get_stock_prices, process_transactions,
                       read_user_settings)


@pytest.mark.parametrize(
    "date_obj, expected",
    [
        (datetime(2022, 1, 10, 9, 30, 12), "Доброе утро"),
        (datetime(2022, 1, 10, 13, 30, 12), "Добрый день"),
        (datetime(2022, 1, 10, 19, 30, 12), "Добрый вечер"),
        (datetime(2022, 1, 10, 1, 30, 12), "Доброй ночи"),
    ],
)
def test_get_greeting(date_obj, expected):
    assert get_greeting(date_obj) == expected


@patch("requests.request")
def test_get_exchange_rates(mock_request):
    mock_request.return_value.json.return_value = {
        "date": "2018-02-22",
        "historical": "",
        "info": {"rate": 148.972231, "timestamp": 1519328414},
        "query": {"amount": 1, "from": "USD", "to": "RUB"},
        "result": 100.12,
        "success": True,
    }
    mocked_open = mock_open(read_data='{"user_currencies": ["USD"], "user_stocks": ["AAPL"]}')
    with patch("builtins.open", mocked_open):
        result = get_exchange_rates(datetime.datetime(2018, 2, 22, 12, 0, 0))
        assert result == [{"currency": "USD", "rate": 100.12}]


@pytest.fixture
def mock_os_path_exists():
    with patch("os.path.exists") as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_load_dotenv():
    with patch("src.utils.load_dotenv", return_value=None):
        yield


@pytest.fixture
def mock_getenv():
    with patch("os.getenv", return_value="test_api_key") as mock_env:
        yield mock_env


@pytest.mark.parametrize("file_exists, expected_exception", [(False, FileNotFoundError)])
def test_read_user_settings_file_not_found(mock_os_path_exists, file_exists, expected_exception):
    mock_os_path_exists.return_value = file_exists
    if not file_exists:
        with pytest.raises(expected_exception) as excinfo:
            read_user_settings("test_user_settings.json")
        assert "Файл настроек test_user_settings.json не найден." in str(excinfo.value)


@pytest.mark.parametrize("file_exists, expected_len", [(True, 2)])
def test_get_operations_data(mock_os_path_exists, file_exists, expected_len):
    mock_os_path_exists.return_value = file_exists
    with patch(
        "src.utils.pd.read_excel",
        return_value=pd.DataFrame(
            {
                "Дата операции": ["01-01-2022", "02-01-2022"],
                "Категория": ["Еда", "Развлечения"],
                "Описание": ["Покупка продуктов", "Кино"],
                "Сумма": [100, 200],
            }
        ),
    ):
        df = get_operations_data("test_path.xlsx")
    assert len(df) == expected_len


@pytest.mark.parametrize("file_exists, expected_exception", [(False, FileNotFoundError)])
def test_get_operations_data_file_not_found(mock_os_path_exists, file_exists, expected_exception):
    mock_os_path_exists.return_value = file_exists
    if not file_exists:
        with pytest.raises(expected_exception) as excinfo:
            get_operations_data("test_path.xlsx")
        assert "Файл данных test_path.xlsx не найден." in str(excinfo.value)


@pytest.mark.parametrize(
    "transactions, expected_cards, expected_top",
    [
        (
            {
                "Дата операции": pd.to_datetime(["2022-01-01", "2022-01-02"]),
                "Номер карты": ["1234", "5678"],
                "Сумма операции": [100, 200],
                "Кэшбэк": [5, 10],
            },
            2,
            2,
        )
    ],
)
def test_process_transactions(transactions, expected_cards, expected_top):
    df = pd.DataFrame(transactions)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 31)
    cards_result, top_transactions = process_transactions(df, start_date, end_date)
    assert len(cards_result) == expected_cards
    assert len(top_transactions) == expected_top


@pytest.mark.parametrize(
    "api_response, expected_rates",
    [({"rates": {"RUB": 74.5, "EUR": 0.9}}, {"USD": 74.5, "EUR": 82.78})],
)
def test_get_exchange_rates(mock_requests_get, mock_load_dotenv, mock_getenv, api_response, expected_rates):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = api_response
    rates = get_exchange_rates(["USD", "EUR"])
    assert rates["USD"] == expected_rates["USD"]
    assert round(rates["EUR"], 2) == expected_rates["EUR"]


@pytest.mark.parametrize("status_code", [500])
def test_get_exchange_rates_api_error(mock_requests_get, mock_load_dotenv, mock_getenv, status_code):
    mock_requests_get.return_value.status_code = status_code
    mock_requests_get.return_value.text = "Internal Server Error"
    rates = get_exchange_rates(["USD", "EUR"])
    assert rates["USD"] is None
    assert rates["EUR"] is None


@pytest.mark.parametrize(
    "api_response, expected_price",
    [
        (
            {"Time Series (5min)": {"2022-01-10 20:00:00": {"4. close": "150.00"}}},
            "150.00",
        )
    ],
)
def test_get_stock_prices(mock_requests_get, mock_load_dotenv, mock_getenv, api_response, expected_price):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = api_response
    prices = get_stock_prices(["AAPL"])
    assert prices["AAPL"] == expected_price


@pytest.mark.parametrize("api_response", [{}])
def test_get_stock_prices_invalid_response(mock_requests_get, mock_load_dotenv, mock_getenv, api_response):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = api_response
    prices = get_stock_prices(["AAPL"])
    assert prices["AAPL"] is None
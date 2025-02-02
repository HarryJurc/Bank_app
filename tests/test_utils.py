import pytest
import json
import os
from datetime import datetime
from unittest.mock import patch, mock_open
import pandas as pd
from src.utils import get_greeting, read_user_settings, get_operations_data, process_transactions, get_exchange_rates, get_stock_prices

def test_get_greeting():
    dt = datetime(2022, 1, 10, 8, 0, 0)
    assert get_greeting(dt) == "Доброе утро"
    dt = datetime(2022, 1, 10, 14, 0, 0)
    assert get_greeting(dt) == "Добрый день"
    dt = datetime(2022, 1, 10, 19, 0, 0)
    assert get_greeting(dt) == "Добрый вечер"
    dt = datetime(2022, 1, 10, 2, 0, 0)
    assert get_greeting(dt) == "Доброй ночи"

def test_read_user_settings(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=json.dumps({"user_currencies": ["USD"], "user_stocks": ["AAPL"]})))
    settings = read_user_settings("test_user_settings.json")
    assert settings["user_currencies"] == ["USD"]
    assert settings["user_stocks"] == ["AAPL"]

def test_read_user_settings_file_not_found(mocker):
    mocker.patch("os.path.exists", return_value=False)
    with pytest.raises(FileNotFoundError) as excinfo:
        read_user_settings("test_user_settings.json")
    assert "Файл настроек test_user_settings.json не найден." in str(excinfo.value)

def test_get_operations_data(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("src.utils.pd.read_excel", return_value=pd.DataFrame({
        "Дата операции": ["01-01-2022", "02-01-2022"],
        "Категория": ["Еда", "Развлечения"],
        "Описание": ["Покупка продуктов", "Кино"],
        "Сумма": [100, 200]
    }))
    df = get_operations_data("test_path.xlsx")
    assert len(df) == 2

def test_get_operations_data_file_not_found(mocker):
    mocker.patch("os.path.exists", return_value=False)
    with pytest.raises(FileNotFoundError) as excinfo:
        get_operations_data("test_path.xlsx")
    assert "Файл данных test_path.xlsx не найден." in str(excinfo.value)

def test_process_transactions():
    df = pd.DataFrame({
        "Дата операции": pd.to_datetime(["2022-01-01", "2022-01-02"]),
        "Номер карты": ["1234", "5678"],
        "Сумма операции": [100, 200],
        "Кэшбэк": [5, 10]
    })
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 1, 31)
    cards_result, top_transactions = process_transactions(df, start_date, end_date)
    assert len(cards_result) == 2
    assert len(top_transactions) == 2

def test_get_exchange_rates(mocker):
    mocker.patch("src.utils.load_dotenv", return_value=None)
    mocker.patch("os.getenv", return_value="test_api_key")
    mocker
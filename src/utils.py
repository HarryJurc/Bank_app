import json
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_greeting(dt: datetime) -> str:
    """Возвращает приветствие в зависимости от времени суток."""

    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def read_user_settings(settings_path: str = "../user_settings.json") -> dict[str, Any]:
    """Читает пользовательские настройки из указанного JSON файла."""

    logging.info(f"Чтение настроек из файла {settings_path}")
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Файл настроек {settings_path} не найден.")
    with open(settings_path, "r", encoding="utf-8") as f:
        settings: dict[str, Any] = json.load(f)
        return settings


def get_operations_data(filepath: str = "../data/operations.xlsx") -> pd.DataFrame:
    """Читает данные операций из указанного файла Excel."""

    logging.info(f"Чтение данных из файла {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл данных {filepath} не найден.")

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    return df


def process_transactions(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> tuple:
    """Обрабатывает транзакции, фильтруя их по указанному диапазону дат."""

    logging.info(f"Фильтрация транзакций с {start_date} по {end_date}")
    df_filtered = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

    cards_summary = df_filtered.groupby("Номер карты").agg({"Сумма операции": "sum", "Кэшбэк": "sum"}).reset_index()

    cards_summary["Номер карты"] = cards_summary["Номер карты"].astype(str).str[-4:]

    top_transactions = df_filtered.nlargest(5, "Сумма операции")
    top_transactions["Дата операции"] = top_transactions["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return cards_summary.to_dict(orient="records"), top_transactions.to_dict(orient="records")


def get_exchange_rates(currencies: list) -> dict:
    """Получает курсы валют (USD и EUR к RUB) с exchangerates_data API от apilayer"""

    load_dotenv()
    api_key_currency = os.getenv("API_KEY_CURRENCY")

    if not api_key_currency:
        raise ValueError("API_KEY_CURRENCY не найден. Проверь .env!")

    url = f"https://api.apilayer.com/exchangerates_data/latest?apikey={api_key_currency}"

    try:
        logging.info(f"Запрос курсов валют для: {currencies}")
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"Ошибка API: {response.status_code}, {response.text}")

        data = response.json()
        logging.info(f"Ответ от API курса валют: {data}")

        if "rates" not in data or "RUB" not in data["rates"]:
            raise ValueError("Ключ 'rates' отсутствует или нет RUB в ответе API.")

        usd_to_rub = data["rates"]["RUB"]
        eur_to_rub = usd_to_rub / data["rates"]["EUR"]

        rates = {currency: None for currency in currencies}
        if "USD" in currencies:
            rates["USD"] = usd_to_rub
        if "EUR" in currencies:
            rates["EUR"] = eur_to_rub

        return rates

    except Exception as e:
        logging.error(f"Ошибка при запросе курсов валют: {e}")
        return {currency: None for currency in currencies}


def get_stock_prices(stocks: list) -> dict:
    """Получает цены акций с Alpha Vantage API"""

    load_dotenv()
    api_key = os.getenv("API_KEY_STOCK")
    stock_prices = {}

    try:
        for stock in stocks:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={stock}&interval=5min&apikey={api_key}"
            logging.info(f"Запрос данных для акций: {stock}")
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                raise ValueError(f"Ошибка API: {response.status_code}, {response.text}")

            data = response.json()
            logging.info(f"Ответ от API для {stock}: {data}")

            if "Time Series (5min)" in data:
                latest_time = next(iter(data["Time Series (5min)"].keys()))
                stock_prices[stock] = data["Time Series (5min)"][latest_time]["4. close"]
            else:
                stock_prices[stock] = None

    except Exception as e:
        logging.error(f"Ошибка при запросе данных для акций: {e}")

    return stock_prices

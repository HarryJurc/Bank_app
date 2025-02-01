import json
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_greeting(dt: datetime) -> str:
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
    logging.info(f"Чтение настроек из файла {settings_path}")
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Файл настроек {settings_path} не найден.")
    with open(settings_path, "r", encoding="utf-8") as f:
        settings: dict[str, Any] = json.load(f)
        return settings

def get_operations_data(filepath: str = "../data/operations.xlsx") -> pd.DataFrame:
    logging.info(f"Чтение данных из файла {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл данных {filepath} не найден.")

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    return df


def process_transactions(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> tuple:
    logging.info(f"Фильтрация транзакций с {start_date} по {end_date}")
    df_filtered = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

    cards_summary = df_filtered.groupby("Номер карты").agg({"Сумма операции": "sum", "Кэшбэк": "sum"}).reset_index()

    cards_summary["Номер карты"] = cards_summary["Номер карты"].astype(str).str[-4:]

    top_transactions = df_filtered.nlargest(5, "Сумма операции")
    top_transactions["Дата операции"] = top_transactions["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return cards_summary.to_dict(orient="records"), top_transactions.to_dict(orient="records")


def get_exchange_rates(currencies: list) -> dict:
    api_key_currency = os.getenv("API_KEY_CURRENCY")
    url = f"https://openexchangerates.org/api/latest.json?app_id={api_key_currency}"
    try:
        logging.info(f"Запрос курсов валют для: {currencies}")
        response = requests.get(url, timeout=10)
        data = response.json()
        logging.info(f"Ответ от API курса валют: {data}")
        if "rates" not in data:
            raise ValueError("Ключ 'rates' отсутствует в ответе API.")

        usd_to_rub = data["rates"]["RUB"]
        eur_to_rub = data["rates"]["RUB"] / data["rates"]["EUR"]

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
    stock_prices = {}
    api_key = os.getenv("API_KEY_STOCK")
    url = f"https://www.alphavantage.co/query?function=BATCH_STOCK_QUOTES&apikey={api_key}&symbols={','.join(stocks)}"
    try:
        logging.info(f"Запрос цены акций для: {stocks}")
        response = requests.get(
            url,
            params={"function": "BATCH_STOCK_QUOTES", "symbols": ",".join(stocks), "apikey": api_key},
            timeout=10,
        )
        data = response.json()
        logging.info(f"Ответ от API цены акций: {data}")
        for stock in stocks:
            stock_data = next((quote for quote in data["Stock Quotes"] if quote["1. symbol"] == stock), None)
            if stock_data:
                stock_prices[stock] = stock_data.get("2. price", None)
            else:
                stock_prices[stock] = None
    except Exception as e:
        logging.error(f"Ошибка при запросе цены акций для {stocks}: {e}")
        stock_prices = {stock: None for stock in stocks}
    return stock_prices

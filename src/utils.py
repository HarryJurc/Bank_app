# import os
#
# import pandas as pd
# from datetime import datetime
#
# import requests
#
#
# def get_greeting(datetime_str):
#     try:
#         dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
#         hour = dt.hour
#         if 5 <= hour < 12:
#             return "Доброе утро"
#         elif 12 <= hour < 18:
#             return "Добрый день"
#         elif 18 <= hour < 22:
#             return "Добрый вечер"
#         else:
#             return "Доброй ночи"
#     except ValueError:
#         return "Неверный формат даты"
#
#
# def process_transactions(df):
#     cards = {}
#     for _, row in df.iterrows():
#         card_number = str(row["Номер карты"]).replace("*", "") if not pd.isna(row["Номер карты"]) else "0000"
#         amount = abs(float(row["Сумма операции"]))
#         if card_number not in cards:
#             cards[card_number] = {"last_digits": card_number, "total_spent": 0, "cashback": 0}
#         cards[card_number]["total_spent"] += amount
#         cards[card_number]["cashback"] = round(cards[card_number]["total_spent"] * 0.01, 2)
#         return list(cards.values())
#
#
# def get_top_transactions(df, n=5):
#     df_sorted = df.sort_values(by="Сумма операции", ascending=True).head(n)
#     return df_sorted[["Дата операции", "Сумма операции", "Категория", "Описание"]].to_dict(orient="records")
#
#
# def read_excel_data(file_path):
#     df_operations = pd.read_excel(file_path, sheet_name="Отчет по операциям")
#     df_operations = df_operations[df_operations["Статус"] == "OK"]
#     return df_operations
#
#
# def fetch_currency_rates(currencies):
#     api_key = os.getenv("API_KEY_CURRENCY")
#     url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"
#
#     headers = {"Authorization": f"Bearer {api_key}"}
#
#     response = requests.get(url, headers=headers)
#
#     if response.status_code == 200:
#         try:
#             rates = response.json().get("rates", {})
#             return [{"currency": cur, "rate": rates.get(cur, "Нет данных")} for cur in currencies]
#         except ValueError:
#             return [{"currency": cur, "rate": "Ошибка в данных API"} for cur in currencies]
#     else:
#         return [{"currency": cur, "rate": "Ошибка API"} for cur in currencies]
#
#
# def fetch_stock_prices(stocks):
#     api_key = "API_KEY_STOCK"
#     base_url = "https://www.alphavantage.co/query"
#     stock_prices = []
#
#     for stock in stocks:
#         params = {
#             "function": "GLOBAL_QUOTE",
#             "symbol": stock,
#             "apikey": api_key
#         }
#         response = requests.get(base_url, params=params)
#         if response.status_code == 200:
#             data = response.json().get("Global Quote", {})
#             price = data.get("05. price", "Нет данных")
#             stock_prices.append({"stock": stock, "price": float(price) if price != "Нет данных" else price})
#         else:
#             stock_prices.append({"stock": stock, "price": "Ошибка API"})
#
#     return stock_prices

import json
import requests
import pandas as pd
from datetime import datetime
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


def read_user_settings(settings_path: str = "../user_settings.json") -> dict:
    logging.info(f"Чтение настроек из файла {settings_path}")
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Файл настроек {settings_path} не найден.")
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_operations_data(filepath: str = "../data/operations.xlsx") -> pd.DataFrame:
    logging.info(f"Чтение данных из файла {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл данных {filepath} не найден.")

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors='coerce', dayfirst=True)
    return df


def process_transactions(df: pd.DataFrame, start_date: datetime, end_date: datetime):
    logging.info(f"Фильтрация транзакций с {start_date} по {end_date}")
    df_filtered = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

    cards_summary = df_filtered.groupby("Номер карты").agg({
        "Сумма операции": "sum",
        "Кэшбэк": "sum"
    }).reset_index()

    cards_summary["Номер карты"] = cards_summary["Номер карты"].astype(str).str[-4:]

    top_transactions = df_filtered.nlargest(5, "Сумма операции")
    top_transactions["Дата операции"] = top_transactions["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S")

    return cards_summary.to_dict(orient="records"), top_transactions.to_dict(orient="records")


def get_exchange_rates(currencies: list) -> dict:
    api_key_currency = os.getenv('API_KEY_CURRENCY')
    url = f"https://openexchangerates.org/api/latest.json?app_id=0a6503c59c9944e285b8e246c2fb4c15"
    try:
        logging.info(f"Запрос курсов валют для: {currencies}")
        response = requests.get(url, timeout=10)
        data = response.json()
        logging.info(f"Ответ от API курса валют: {data}")
        if 'rates' not in data:
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
    api_key_stock = os.getenv('API_KEY_STOCK')
    base_url = f"https://www.alphavantage.co/query?function=BATCH_STOCK_QUOTES&apikey={api_key_stock}&symbols={','.join(stocks)}"
    try:
        logging.info(f"Запрос цены акций для: {stocks}")
        response = requests.get(base_url, params={
            "function": "BATCH_STOCK_QUOTES",
            "symbols": ','.join(stocks),
            "apikey": api_key_stock
        }, timeout=10)
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

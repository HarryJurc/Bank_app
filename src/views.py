import json
import logging

import pandas as pd
from datetime import datetime
from utils import get_greeting, process_transactions, get_operations_data, read_user_settings, get_exchange_rates, \
    get_stock_prices
import os


def main(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        logging.info(f"Парсинг даты: {dt}")
    except Exception:
        return json.dumps({"error": "Неверный формат даты. Ожидается YYYY-MM-DD HH:MM:SS"})

    greeting = get_greeting(dt)
    logging.info(f"Приветствие: {greeting}")

    start_date = dt.replace(day=1, hour=0, minute=0, second=0)
    end_date = dt

    try:
        df = get_operations_data()
    except FileNotFoundError as e:
        logging.error(f"Ошибка: {e}")
        return json.dumps({"error": str(e)})

    cards_result, top_transactions = process_transactions(df, start_date, end_date)
    logging.info(f"Данные по картам: {cards_result}")
    logging.info(f"Топ-5 транзакций: {top_transactions}")

    try:
        settings = read_user_settings()
        user_currencies = settings.get("user_currencies", [])
        user_stocks = settings.get("user_stocks", [])
    except FileNotFoundError as e:
        logging.error(f"Ошибка: {e}")
        return json.dumps({"error": str(e)})

    exchange_rates = get_exchange_rates(user_currencies) if user_currencies else {}
    logging.info(f"Курсы валют: {exchange_rates}")

    stocks = get_stock_prices(user_stocks) if user_stocks else {}
    logging.info(f"Цены акций: {stocks}")

    result = {
        "greeting": greeting,
        "cards": cards_result,
        "top_transactions": top_transactions,
        "exchange_rates": exchange_rates,
        "stocks": stocks
    }

    logging.info("Формирование итогового результата")
    return json.dumps(result, ensure_ascii=False, indent=2)


# Тестовый вызов
if __name__ == "__main__":
    input_date = "2020-01-31 15:30:00"
    print(main(input_date))
import json
import logging
from datetime import datetime

from src.utils import (
    get_exchange_rates,
    get_greeting,
    get_operations_data,
    get_stock_prices,
    process_transactions,
    read_user_settings,
)


def main(date_str: str) -> str:
    """Основная функция, обрабатывающая операции и возвращающая данные в формате JSON."""

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        logging.info(f"Парсинг даты: {dt}")
    except ValueError:
        return json.dumps({"error": "Неверный формат даты. Ожидается YYYY-MM-DD HH:MM:SS"})

    greeting = get_greeting(dt)
    logging.info(f"Приветствие: {greeting}")

    start_date = dt.replace(day=1, hour=0, minute=0, second=0)
    end_date = dt

    try:
        df = get_operations_data()
        cards_result, top_transactions = process_transactions(df, start_date, end_date)
    except FileNotFoundError as e:
        logging.error(f"Ошибка: {e}")
        return json.dumps({"error": str(e)})

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
        "stocks": stocks,
    }

    logging.info("Формирование итогового результата")
    return json.dumps(result, ensure_ascii=False, indent=2)


# # Тестовый вызов
# if __name__ == "__main__":
#     input_date = "2020-01-31 15:30:00"
#     print(main(input_date))

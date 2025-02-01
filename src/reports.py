import datetime
import json
import logging
import os
from typing import Callable, Optional, Any, TextIO

import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def save_report(filename: Optional[str] = None) -> Callable[[Callable[..., pd.DataFrame]], Callable[..., pd.DataFrame]]:
    def decorator(func: Callable[..., pd.DataFrame]) -> Callable[..., pd.DataFrame]:
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result = func(*args, **kwargs)
            # Преобразование столбца с датами в строковый формат
            result["Дата операции"] = result["Дата операции"].dt.strftime("%Y-%m-%d %H:%М:%С")
            if filename:
                file = filename
            else:
                file = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(orient='records'), f, ensure_ascii=False, indent=2)
            return result
        return wrapper
    return decorator


def get_operations_data(filepath: str = "../data/operations.xlsx") -> pd.DataFrame:
    logging.info(f"Чтение данных из файла {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл данных {filepath} не найден.")

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    logging.info(f"Загружено строк: {len(df)}")
    logging.info(f"Пример данных: {df.head()}")
    logging.info(f"Уникальные категории: {df['Категория'].unique()}")
    logging.info(f"Диапазон дат: от {df['Дата операции'].min()} до {df['Дата операции'].max()}")
    return df


@save_report()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    if date:
        end_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    else:
        end_date = datetime.datetime.now()

    start_date = end_date - datetime.timedelta(days=90)
    logging.info(f"Фильтрация данных с {start_date} по {end_date} для категории {category}")

    mask = (
        (transactions["Дата операции"] >= start_date)
        & (transactions["Дата операции"] <= end_date)
        & (transactions["Категория"] == category)
    )
    filtered_transactions = transactions[mask]

    logging.info(f"Найдено строк: {len(filtered_transactions)}")

    return filtered_transactions


# Пример вызова функции
if __name__ == "__main__":
    try:
        df = get_operations_data()
    except FileNotFoundError as e:
        logging.error(f"Ошибка: {e}")
        exit(1)

    category = "Супермаркеты"
    date = "2021-12-31"
    result_df = spending_by_category(df, category, date)
    print(result_df)

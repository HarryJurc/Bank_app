import json
import logging
import os

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_operations_data(filepath: str = "../data/operations.xlsx") -> pd.DataFrame:
    """Читает данные операций из указанного файла Excel."""

    logging.info(f"Чтение данных из файла {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Файл данных {filepath} не найден.")

    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
    return df


def search_transactions(query: str, filepath: str = "../data/operations.xlsx") -> str:
    """Ищет транзакции по запросу в указанном файле Excel."""

    try:
        df = get_operations_data(filepath)
    except FileNotFoundError as e:
        logging.error(f"Ошибка: {e}")
        return json.dumps({"error": str(e)})

    df_filtered = df[
        (df["Описание"].str.contains(query, case=False, na=False))
        | (df["Категория"].str.contains(query, case=False, na=False))
    ]

    logging.info(f"Найдено транзакций: {len(df_filtered)}")

    df_filtered["Дата операции"] = df_filtered["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S")

    result = df_filtered.to_dict(orient="records")
    return json.dumps(result, ensure_ascii=False, indent=2)


# # Пример вызова функции
# if __name__ == "__main__":
#     search_query = "Супермаркет"
#     print(search_transactions(search_query))

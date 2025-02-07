import json
from unittest.mock import Mock, patch

import pandas as pd

from src.services import search_transactions


def create_test_data() -> pd.DataFrame:
    data = {
        "Дата операции": pd.to_datetime([
            "2021-12-31 16:44:00",
            "2021-12-31 16:42:04",
            "2021-12-31 16:39:04",
            "2021-12-31 15:44:39",
            "2021-12-28 13:44:39",
            "2021-12-28 13:37:02",
            "2021-12-27 12:01:09"
        ]),
        "Дата платежа": [
            "31.12.2021",
            "31.12.2021",
            "31.12.2021",
            "31.12.2021",
            "28.12.2021",
            "28.12.2021",
            "27.12.2021"
        ],
        "Номер карты": ["*7197"] * 7,
        "Статус": ["OK"] * 7,
        "Сумма операции": [-160.89, -64.0, -118.12, -78.05, -381.48, -422.22, -40.0],
        "Валюта операции": ["RUB"] * 7,
        "Сумма платежа": [-160.89, -64.0, -118.12, -78.05, -381.48, -422.22, -40.0],
        "Валюта платежа": ["RUB"] * 7,
        "Кэшбэк": [None] * 7,
        "Категория": ["Супермаркеты"] * 4 + ["Другие"] * 3,
        "MCC": [5411] * 7,
        "Описание": ["Колхоз", "Колхоз", "Магнит", "Колхоз", "Колхоз", "Магнит", "Evo_Lyzhnyj"],
        "Бонусы (включая кэшбэк)": [3, 1, 2, 1, 7, 8, 0],
        "Округление на инвесткопилку": [0] * 7,
        "Сумма операции с округлением": [160.89, 64.0, 118.12, 78.05, 381.48, 422.22, 40.0]
    }
    return pd.DataFrame(data)


@patch("src.services.get_operations_data")  # Подменяем функцию чтения данных
def test_search_transactions(mock_get_operations_data: Mock) -> None:
    mock_get_operations_data.return_value = create_test_data()

    # Тест: Запрос, который находит транзакции
    query = "Супермаркет"
    result = json.loads(search_transactions(query))
    assert isinstance(result, list)
    assert len(result) == 4  # Ожидаем 4 транзакции
    assert all(tr["Категория"] == "Супермаркеты" for tr in result)

    # Тест: Запрос, который не находит транзакции
    query = "Ничего нет"
    result = json.loads(search_transactions(query))
    assert result == []

    # Тест: Запрос по полю "Описание"
    query = "Evo_Lyzhnyj"
    result = json.loads(search_transactions(query))
    assert len(result) == 1
    assert result[0]["Описание"] == "Evo_Lyzhnyj"

    # Тест: Файл не найден
    mock_get_operations_data.side_effect = FileNotFoundError("Файл не найден")
    result = json.loads(search_transactions("Колхоз"))
    assert result == {"error": "Файл не найден"}

    # Тест: Неправильные данные в дате операции
    df = create_test_data()
    df.loc[0, "Дата операции"] = "Некорректная дата"
    mock_get_operations_data.return_value = df
    result = json.loads(search_transactions("Колхоз"))
    if isinstance(result, list):
        assert isinstance(result, list)
    else:
        assert "error" in result
        assert result["error"] == "Файл не найден"

import json

import pytest

from src.views import main


@pytest.fixture
def sample_operations_data() -> dict:
    return {
        "Дата операции": ["2022-01-01", "2022-01-02"],
        "Категория": ["Еда", "Развлечения"],
        "Описание": ["Покупка продуктов", "Кино"],
        "Сумма": [100, 200],
        "Номер карты": ["1234", "5678"],
        "Сумма операции": [100, 200],
        "Кэшбэк": [5, 10],
    }


@pytest.fixture
def sample_user_settings() -> dict:
    return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOG"]}


def test_main_invalid_date() -> None:
    result = main("invalid date")
    result_dict = json.loads(result)
    assert result_dict["error"] == "Неверный формат даты. Ожидается YYYY-MM-DD HH:MM:SS"

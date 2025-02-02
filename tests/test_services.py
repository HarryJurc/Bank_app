import pytest
import pandas as pd
import json
from unittest.mock import patch
from src.services import get_operations_data, search_transactions

@pytest.fixture
def sample_data():
    data = {
        "Дата операции": ["01-01-2022", "02-01-2022"],
        "Категория": ["Еда", "Развлечения"],
        "Описание": ["Покупка продуктов", "Кино"],
        "Сумма": [100, 200]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    return df


def test_get_operations_data(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("src.services.pd.read_excel", return_value=pd.DataFrame({
        "Дата операции": ["01-01-2022", "02-01-2022"],
        "Категория": ["Еда", "Развлечения"],
        "Описание": ["Покупка продуктов", "Кино"],
        "Сумма": [100, 200]
    }))
    result = get_operations_data("test_path.xlsx")
    assert len(result) == 2
    assert "Дата операции" in result.columns
    assert "Категория" in result.columns


def test_get_operations_data_file_not_found(mocker):
    mocker.patch("os.path.exists", return_value=False)
    with pytest.raises(FileNotFoundError) as excinfo:
        get_operations_data("test_path.xlsx")
    assert "Файл данных test_path.xlsx не найден." in str(excinfo.value)


def test_search_transactions_found(mocker, sample_data):
    mocker.patch("src.services.get_operations_data", return_value=sample_data)
    result = search_transactions("еда", "test_path.xlsx")
    assert '"Категория": "Еда"' in result
    assert '"Описание": "Покупка продуктов"' in result


def test_search_transactions_not_found(mocker, sample_data):
    mocker.patch("src.services.get_operations_data", return_value=sample_data)
    result = search_transactions("не существующая категория", "test_path.xlsx")
    assert result == '[]'


def test_search_transactions_partial_match(mocker, sample_data):
    mocker.patch("src.services.get_operations_data", return_value=sample_data)
    result = search_transactions("покупка", "test_path.xlsx")
    assert '"Категория": "Еда"' in result
    assert '"Описание": "Покупка продуктов"' in result


def test_search_transactions_file_not_found(mocker):
    mocker.patch("os.path.exists", return_value=False)
    result = search_transactions("еда", "test_path.xlsx")
    error_response = json.loads(result)
    assert "error" in error_response
    assert error_response["error"] == "Файл данных test_path.xlsx не найден."

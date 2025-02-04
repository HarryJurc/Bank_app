import pytest
from unittest.mock import Mock
import pandas as pd
import json
from src.services import get_operations_data, search_transactions


@pytest.fixture
def sample_data() -> pd.DataFrame:
    data = {
        "Дата операции": ["01-01-2022", "02-01-2022"],
        "Категория": ["Еда", "Развлечения"],
        "Описание": ["Покупка продуктов", "Кино"],
        "Сумма": [100, 200],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    return df


@pytest.fixture
def mock_os_path_exists(mocker: Mock) -> Mock:
    return mocker.patch("os.path.exists", return_value=True)


@pytest.fixture
def mock_read_excel(mocker: Mock) -> Mock:
    return mocker.patch(
        "pandas.read_excel",
        return_value=pd.DataFrame(
            {
                "Дата операции": ["01-01-2022", "02-01-2022"],
                "Категория": ["Еда", "Развлечения"],
                "Описание": ["Покупка продуктов", "Кино"],
                "Сумма": [100, 200],
            }
        ),
    )


# Параметризация для теста get_operations_data
@pytest.mark.parametrize(
    "file_exists, expected_length, expected_columns",
    [
        (True, 2, ["Дата операции", "Категория", "Описание", "Сумма"]),
        (False, 0, []),
    ]
)
def test_get_operations_data(file_exists: bool, expected_length: int, expected_columns: list,
                             mock_os_path_exists, mock_read_excel) -> None:
    mock_os_path_exists.return_value = file_exists
    if file_exists:
        result = get_operations_data("test_path.xlsx")
        assert len(result) == expected_length
        for col in expected_columns:
            assert col in result.columns
    else:
        with pytest.raises(FileNotFoundError):
            get_operations_data("test_path.xlsx")


# Для поиска потенциальных ошибок можно добавить явные проверки
@pytest.mark.parametrize(
    "search_term, expected_result",
    [
        ("еда",
         [{"Дата операции": "2022-01-01 00:00:00", "Категория": "Еда", "Описание": "Покупка продуктов", "Сумма": 100}]),
        ("не существующая категория", []),
        ("покупка",
         [{"Дата операции": "2022-01-01 00:00:00", "Категория": "Еда", "Описание": "Покупка продуктов", "Сумма": 100}]),
    ]
)
def test_search_transactions(mocker: Mock, sample_data: pd.DataFrame, search_term: str, expected_result: list) -> None:
    mocker.patch("src.services.get_operations_data", return_value=sample_data)
    result = search_transactions(search_term, "test_path.xlsx")
    result_json = json.loads(result)  # Преобразуем результат в JSON
    assert result_json == expected_result, f"Expected {expected_result} but got {result_json}"


def test_search_transactions_file_not_found(mocker: Mock) -> None:
    mocker.patch("os.path.exists", return_value=False)
    result = search_transactions("еда", "test_path.xlsx")
    error_response = json.loads(result)
    assert "error" in error_response
    assert error_response["error"] == "Файл данных test_path.xlsx не найден."

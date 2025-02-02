from unittest.mock import Mock, mock_open

import pandas as pd
import pytest

from src.reports import get_operations_data, save_report, spending_by_category


@pytest.fixture
def sample_data() -> pd.DataFrame:
    data = {"Дата операции": ["01-01-2022", "02-01-2022"], "Категория": ["Еда", "Развлечения"], "Сумма": [100, 200]}
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    return df


def test_get_operations_data(mocker: Mock) -> None:
    mocker.patch(
        "src.reports.pd.read_excel",
        return_value=pd.DataFrame(
            {"Дата операции": ["01-01-2022", "02-01-2022"], "Категория": ["Еда", "Развлечения"], "Сумма": [100, 200]}
        ),
    )
    mocker.patch("os.path.exists", return_value=True)
    result = get_operations_data("test_path.xlsx")
    assert len(result) == 2
    assert "Дата операции" in result.columns
    assert "Категория" in result.columns


def test_save_report_decorator(mocker: Mock, sample_data: pd.DataFrame) -> None:
    @save_report("test_report.json")
    def test_func() -> pd.DataFrame:
        return sample_data

    mocker.patch("builtins.open", mock_open())
    result = test_func()
    open.assert_called_once_with("test_report.json", "w", encoding="utf-8")
    assert len(result) == 2


def test_spending_by_category(sample_data: pd.DataFrame) -> None:
    sample_data["Дата операции"] = pd.to_datetime(sample_data["Дата операции"], dayfirst=True)
    result = spending_by_category(sample_data, "Еда", "2022-03-01")
    assert len(result) == 1
    assert (result["Категория"] == "Еда").all()
    assert (pd.to_datetime(result["Дата операции"]) >= pd.Timestamp("2021-12-01")).all()
    assert (pd.to_datetime(result["Дата операции"]) <= pd.Timestamp("2022-03-01")).all()

from datetime import datetime
from unittest.mock import patch, mock_open

import pandas as pd
import pytest
from src.reports import get_operations_data, save_report, spending_by_category


@pytest.fixture
def sample_data() -> pd.DataFrame:
    data = {
        "Дата операции": ["01-01-2022", "02-01-2022"],
        "Категория": ["Еда", "Развлечения"],
        "Сумма": [100, 200]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    return df


@pytest.fixture
def mock_os_path_exists():
    with patch("src.reports.os.path.exists", return_value=True) as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_read_excel():
    with patch("src.reports.pd.read_excel") as mock_excel:
        def mock_read(filepath, *args, **kwargs):
            if filepath == "empty.xlsx":
                return pd.DataFrame()  # Пустой DataFrame
            return pd.DataFrame(
                {"Дата операции": ["01-01-2022", "02-01-2022"], "Категория": ["Еда", "Развлечения"],
                 "Сумма": [100, 200]}
            )

        mock_excel.side_effect = mock_read
        yield mock_excel


@pytest.mark.parametrize(
    "file_path, expected_length",
    [("test_path.xlsx", 2), ("empty.xlsx", 0)],
)
def test_get_operations_data(mock_os_path_exists, mock_read_excel, file_path, expected_length):
    result = get_operations_data(file_path)

    if file_path == "empty.xlsx":
        assert result.empty
    else:
        assert len(result) == expected_length
        assert "Дата операции" in result.columns
        assert "Категория" in result.columns


@pytest.fixture
def mock_open_file():
    with patch("builtins.open", mock_open()) as mock_file:
        yield mock_file


@pytest.mark.parametrize("filename", ["test_report.json", None])
def test_save_report_decorator(mock_open_file, sample_data, filename):
    @save_report(filename)
    def test_func() -> pd.DataFrame:
        return sample_data

    result = test_func()
    if filename:
        mock_open_file.assert_called_once_with(filename, "w", encoding="utf-8")
    assert len(result) == 2


@pytest.mark.parametrize(
    "category, date, expected_length",
    [
        ("Еда", "2022-03-01", 1),
        ("Развлечения", "2022-03-01", 1),
        ("Транспорт", "2022-03-01", 0),
        ("Еда", None, 0),
    ],
)
def test_spending_by_category(sample_data, category, date, expected_length):
    sample_data["Дата операции"] = pd.to_datetime(sample_data["Дата операции"], dayfirst=True)
    result = spending_by_category(sample_data, category, date)
    assert len(result) == expected_length
    if expected_length > 0:
        assert (result["Категория"] == category).all()
        if date:
            assert (pd.to_datetime(result["Дата операции"]) >= pd.Timestamp("2021-12-01")).all()
            assert (pd.to_datetime(result["Дата операции"]) <= pd.Timestamp(date)).all()

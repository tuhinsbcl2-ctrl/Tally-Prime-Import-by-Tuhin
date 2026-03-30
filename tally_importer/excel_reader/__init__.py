"""Excel reading utilities."""
from __future__ import annotations

from typing import Any

import pandas as pd


def read_excel_sheets(file_path: str) -> list[str]:
    """Return a list of sheet names in the given Excel file."""
    xl = pd.ExcelFile(file_path, engine="openpyxl")
    return xl.sheet_names


def read_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Read a sheet from an Excel file and return a DataFrame.

    Rows with all-NaN values are dropped.
    Column names are stripped of leading/trailing whitespace.
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    return df.reset_index(drop=True)


def get_columns(df: pd.DataFrame) -> list[str]:
    """Return column names of a DataFrame."""
    return list(df.columns)


def get_preview_rows(df: pd.DataFrame, n: int = 10) -> list[dict[str, Any]]:
    """Return the first *n* rows as a list of dicts for UI preview."""
    return df.head(n).fillna("").to_dict(orient="records")

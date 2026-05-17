from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DataInspectionUnavailableError(ValueError):
    pass


@dataclass(frozen=True)
class CsvInspection:
    source: str
    rows: int
    columns: list[str]
    missing_values: dict[str, int]
    numeric_columns: list[str]
    category_columns: list[str]
    numeric_summaries: dict[str, dict[str, float]]
    possible_metrics: list[str]


@dataclass(frozen=True)
class DataInspectionReport:
    files: list[CsvInspection]


def inspect_data_folder(folder: Path) -> DataInspectionReport:
    folder = _require_folder(folder)
    pd, np = _load_dependencies()
    csv_paths = sorted((folder / "data").rglob("*.csv")) if (folder / "data").is_dir() else []
    inspections = [_inspect_csv(path, folder, pd, np) for path in csv_paths]
    return DataInspectionReport(files=inspections)


def format_data_inspection(report: DataInspectionReport) -> str:
    lines = ["Data Inspection", "", "Files:"]
    if not report.files:
        lines.extend(["- None", "", "No CSV files found in data/."])
        return "\n".join(lines).rstrip() + "\n"

    for inspection in report.files:
        lines.append(f"- {inspection.source}")

    for inspection in report.files:
        lines.extend(
            [
                "",
                f"{Path(inspection.source).name}:",
                f"- Source: {inspection.source}",
                f"- Rows: {inspection.rows}",
                f"- Columns: {len(inspection.columns)} ({', '.join(inspection.columns)})",
                f"- Missing values: {_format_missing_values(inspection.missing_values)}",
                f"- Numeric columns: {_format_list(inspection.numeric_columns)}",
                f"- Category/text columns: {_format_list(inspection.category_columns)}",
                "- Numeric summaries:",
                *_format_numeric_summaries(inspection.numeric_summaries),
                "- Possible metrics:",
                *_format_numbered(inspection.possible_metrics),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _inspect_csv(path: Path, folder: Path, pd: Any, np: Any) -> CsvInspection:
    dataframe = pd.read_csv(path)
    numeric_columns = list(dataframe.select_dtypes(include=[np.number]).columns)
    category_columns = [
        column
        for column in dataframe.columns
        if column not in numeric_columns
    ]
    missing_values = {
        column: int(count)
        for column, count in dataframe.isna().sum().items()
        if int(count) > 0
    }
    numeric_summaries = _numeric_summaries(dataframe, numeric_columns, np)
    possible_metrics = _possible_metrics(list(dataframe.columns))
    return CsvInspection(
        source=path.relative_to(folder).as_posix(),
        rows=int(len(dataframe)),
        columns=list(dataframe.columns),
        missing_values=missing_values,
        numeric_columns=numeric_columns,
        category_columns=category_columns,
        numeric_summaries=numeric_summaries,
        possible_metrics=possible_metrics,
    )


def _numeric_summaries(dataframe: Any, numeric_columns: list[str], np: Any) -> dict[str, dict[str, float]]:
    summaries: dict[str, dict[str, float]] = {}
    for column in numeric_columns:
        values = dataframe[column].to_numpy(dtype=float)
        summaries[column] = {
            "mean": float(np.nanmean(values)),
            "min": float(np.nanmin(values)),
            "max": float(np.nanmax(values)),
        }
    return summaries


def _possible_metrics(columns: list[str]) -> list[str]:
    metrics: list[str] = []
    for column in columns:
        lowered = column.lower()
        label = column.replace("_", " ")
        if any(term in lowered for term in ["time", "duration", "minutes", "hours"]):
            metrics.append(f"Average {label}")
        if any(term in lowered for term in ["score", "rating", "satisfaction"]):
            metrics.append(f"Average {label}")
        if any(term in lowered for term in ["status", "priority", "category", "region", "agent"]):
            metrics.append(f"Counts by {label}")
        if any(term in lowered for term in ["revenue", "amount", "price", "cost"]):
            metrics.append(f"Total and average {label}")
    return _unique(metrics)


def _load_dependencies() -> tuple[Any, Any]:
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        raise DataInspectionUnavailableError(
            "pandas and NumPy are required for data inspection.\n"
            "Install them with: pip install pandas numpy"
        ) from exc
    return pd, np


def _require_folder(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"{folder} is not a project folder.")
    return folder


def _format_missing_values(missing_values: dict[str, int]) -> str:
    if not missing_values:
        return "None"
    return ", ".join(f"{column} has {count} missing values" for column, count in missing_values.items())


def _format_list(items: list[str]) -> str:
    if not items:
        return "None"
    return ", ".join(items)


def _format_numeric_summaries(summaries: dict[str, dict[str, float]]) -> list[str]:
    if not summaries:
        return ["  - None"]
    lines: list[str] = []
    for column, summary in summaries.items():
        lines.append(
            f"  - {column}: mean={summary['mean']:.2f}, min={summary['min']:.2f}, max={summary['max']:.2f}"
        )
    return lines


def _format_numbered(items: list[str]) -> list[str]:
    if not items:
        return ["  - None"]
    return [f"  {index}. {item}" for index, item in enumerate(items, start=1)]


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items

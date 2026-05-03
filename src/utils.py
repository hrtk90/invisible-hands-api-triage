"""Shared utility functions for cleaning V&A CSV-style catalogue rows."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = [
    "accessionNumber",
    "accessionYear",
    "systemNumber",
    "objectType",
    "_primaryTitle",
    "_primaryPlace",
    "_primaryMaker__name",
    "_primaryMaker__association",
    "_primaryDate",
    "_primaryImageId",
    "_sampleMaterial",
    "_sampleTechnique",
    "_sampleStyle",
    "_currentLocation__displayName",
    "_objectContentWarning",
    "_imageContentWarning",
]


def has_value(value: object) -> bool:
    """Return True when a catalogue value is meaningfully present."""
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return text != "" and text.lower() not in {"nan", "none", "nat"}


def safe_text(value: object) -> str:
    """Convert missing values to empty strings and trim visible text."""
    if not has_value(value):
        return ""
    return str(value).strip()


def ensure_expected_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add missing V&A CSV columns as empty strings so the app does not crash."""
    if df is None:
        df = pd.DataFrame()

    cleaned = df.copy()
    for column in EXPECTED_COLUMNS:
        if column not in cleaned.columns:
            cleaned[column] = ""

    for column in EXPECTED_COLUMNS:
        cleaned[column] = cleaned[column].fillna("").astype(str)

    return cleaned


def missing_expected_columns(df: pd.DataFrame) -> list[str]:
    """List expected columns absent from the original API response."""
    if df is None:
        return EXPECTED_COLUMNS.copy()
    return [column for column in EXPECTED_COLUMNS if column not in df.columns]


YEAR_PATTERN = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)")


def extract_first_year(value: object) -> int | None:
    """Extract the first four-digit year from a date string, if available."""
    text = safe_text(value)
    if not text:
        return None

    match = YEAR_PATTERN.search(text)
    if match is None:
        return None
    return int(match.group(1))


def filter_by_date_range(
    df: pd.DataFrame,
    made_after_year: int,
    made_before_year: int,
    strict: bool,
) -> pd.DataFrame:
    """Filter by extracted year while preserving uncertain dates when requested."""
    filtered = df.copy()
    years = filtered["_primaryDate"].map(extract_first_year)
    numeric_years = pd.to_numeric(years, errors="coerce")

    in_range = numeric_years.between(
        made_after_year,
        made_before_year,
        inclusive="both",
    )
    if strict:
        mask = numeric_years.notna() & in_range
    else:
        mask = numeric_years.isna() | in_range

    return filtered.loc[mask].copy()


def make_thumbnail_url(image_id: object) -> str:
    """Build the V&A Framemark thumbnail URL for a primary image id."""
    image_text = safe_text(image_id)
    if not image_text:
        return ""
    return (
        "https://framemark.vam.ac.uk/collections/"
        f"{image_text}/full/!100,100/0/default.jpg"
    )


def make_object_page_url(system_number: object) -> str:
    """Build the public V&A Collections object page URL."""
    system_text = safe_text(system_number)
    if not system_text:
        return ""
    return f"https://collections.vam.ac.uk/item/{system_text}/"


def has_usable_rows(df: pd.DataFrame) -> bool:
    """Check whether a dataframe has at least one row with core catalogue content."""
    if df is None or df.empty:
        return False

    core_fields = [
        "systemNumber",
        "objectType",
        "_primaryTitle",
        "_primaryPlace",
        "_primaryMaker__name",
        "_primaryDate",
    ]
    checked = ensure_expected_columns(df)
    for _, row in checked.iterrows():
        if any(has_value(row.get(field, "")) for field in core_fields):
            return True
    return False


def load_sample_records(path: str | Path) -> pd.DataFrame:
    """Load local illustrative fallback records."""
    sample_df = pd.read_csv(path, keep_default_na=False)
    return ensure_expected_columns(sample_df)


def top_nonempty_values(series: pd.Series, limit: int = 5) -> pd.DataFrame:
    """Return a small count table for non-empty values."""
    cleaned = series.map(safe_text)
    cleaned = cleaned[cleaned != ""]
    if cleaned.empty:
        return pd.DataFrame(columns=["value", "count"])

    return (
        cleaned.value_counts()
        .head(limit)
        .rename_axis("value")
        .reset_index(name="count")
    )

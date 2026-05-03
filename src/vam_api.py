"""V&A Collections API CSV loading helpers."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import requests

from src.utils import ensure_expected_columns, missing_expected_columns


API_ENDPOINT = "https://api.vam.ac.uk/v2/objects/search"


def build_api_url(query: str, page_size: int, images_only: bool = False) -> str:
    """Build the exact CSV endpoint URL used by the live request."""
    params = {
        "q": query,
        "page_size": page_size,
        "response_format": "csv",
    }
    if images_only:
        params["images_exist"] = "1"

    request = requests.Request("GET", API_ENDPOINT, params=params).prepare()
    return request.url


def fetch_vam_csv(
    query: str,
    page_size: int,
    images_only: bool = False,
    timeout: int = 20,
) -> tuple[pd.DataFrame, str, list[str]]:
    """Fetch V&A CSV data and return normalized rows plus request metadata."""
    url = build_api_url(query, page_size, images_only)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    if not response.text.strip():
        raise ValueError("The live CSV response was empty.")

    raw_df = pd.read_csv(StringIO(response.text), keep_default_na=False)
    missing = missing_expected_columns(raw_df)
    normalized_df = ensure_expected_columns(raw_df)
    return normalized_df, url, missing

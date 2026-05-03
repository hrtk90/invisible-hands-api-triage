from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.archival_routes import recommend_next_steps
from src.scoring import score_record
from src.utils import (
    EXPECTED_COLUMNS,
    ensure_expected_columns,
    filter_by_date_range,
    has_usable_rows,
    has_value,
    load_sample_records,
    make_object_page_url,
    make_thumbnail_url,
    safe_text,
    top_nonempty_values,
)
from src.vam_api import build_api_url, fetch_vam_csv


SAMPLE_DATA_PATH = Path("data") / "sample_records.csv"

DISPLAY_COLUMNS = [
    "accessionNumber",
    "systemNumber",
    "object_page",
    "objectType",
    "_primaryTitle",
    "_primaryPlace",
    "_primaryMaker__name",
    "_primaryMaker__association",
    "_primaryDate",
    "_sampleMaterial",
    "_sampleTechnique",
    "_currentLocation__displayName",
    "archival_tractability_score",
    "evidence_status",
    "archival_next_steps",
    "evidence_reasons",
]


@st.cache_data(ttl=3600, show_spinner=False)
def load_live_records(query: str, page_size: int, images_only: bool):
    """Cache live V&A API CSV results for one hour."""
    return fetch_vam_csv(query=query, page_size=page_size, images_only=images_only)


def load_fallback_records() -> pd.DataFrame:
    """Load illustrative local fallback rows."""
    return load_sample_records(SAMPLE_DATA_PATH)


def enrich_records(df: pd.DataFrame) -> pd.DataFrame:
    """Add links, scores, labels, reasons, and archival next steps."""
    enriched = ensure_expected_columns(df)
    enriched["object_page"] = enriched["systemNumber"].map(make_object_page_url)
    enriched["thumbnail_url"] = enriched["_primaryImageId"].map(make_thumbnail_url)

    score_rows = enriched.apply(score_record, axis=1, result_type="expand")
    enriched["archival_tractability_score"] = score_rows[
        "archival_tractability_score"
    ]
    enriched["evidence_status"] = score_rows["evidence_status"]
    enriched["evidence_reasons"] = score_rows["evidence_reasons"]
    enriched["archival_next_steps"] = enriched.apply(recommend_next_steps, axis=1)
    return enriched


def render_summary(df: pd.DataFrame) -> None:
    st.subheader("Summary")

    mean_score = 0.0
    if not df.empty:
        mean_score = float(df["archival_tractability_score"].mean())

    metric_cols = st.columns(3)
    metric_cols[0].metric("Records loaded", len(df))
    metric_cols[1].metric("Mean archival tractability score", f"{mean_score:.1f}")
    metric_cols[2].metric("Maximum possible score", "9")

    status_counts = (
        df["evidence_status"]
        .value_counts()
        .rename_axis("evidence_status")
        .reset_index(name="count")
        if not df.empty
        else pd.DataFrame(columns=["evidence_status", "count"])
    )
    st.write("Count by evidence_status")
    st.dataframe(status_counts, hide_index=True, use_container_width=True)

    maker_places = st.columns(2)
    with maker_places[0]:
        st.write("Top maker names")
        makers = top_nonempty_values(df["_primaryMaker__name"]) if not df.empty else None
        if makers is not None and not makers.empty:
            st.dataframe(makers, hide_index=True, use_container_width=True)
        else:
            st.caption("No maker names present in the displayed records.")

    with maker_places[1]:
        st.write("Top places")
        places = top_nonempty_values(df["_primaryPlace"]) if not df.empty else None
        if places is not None and not places.empty:
            st.dataframe(places, hide_index=True, use_container_width=True)
        else:
            st.caption("No places present in the displayed records.")


def render_thumbnails(df: pd.DataFrame) -> None:
    image_rows = df[df["thumbnail_url"].map(has_value)].head(12)
    if image_rows.empty:
        return

    st.subheader("Thumbnails")
    columns = st.columns(4)
    for index, (_, row) in enumerate(image_rows.iterrows()):
        with columns[index % 4]:
            st.image(row["thumbnail_url"], width=100)
            title = safe_text(row.get("_primaryTitle", "")) or "Untitled record"
            maker = safe_text(row.get("_primaryMaker__name", ""))
            date = safe_text(row.get("_primaryDate", ""))
            st.caption(title)
            if maker:
                st.caption(f"Maker: {maker}")
            if date:
                st.caption(f"Date: {date}")
            object_page = safe_text(row.get("object_page", ""))
            if object_page:
                st.markdown(f"[V&A object page]({object_page})")


def main() -> None:
    st.set_page_config(
        page_title="Invisible Hands API Triage",
        layout="wide",
    )

    st.title("Invisible Hands API Triage")
    st.subheader("A V&A Collections API prototype for labour-visibility research")
    st.info(
        "This prototype uses V&A Collections API metadata to identify catalogue "
        "records that may be useful starting points for archival research into "
        "craft labour, attribution, place, material process, and documentation "
        "gaps. It does not identify migrant makers automatically and does not "
        "infer migrant status from names, places, or maker fields alone."
    )

    st.sidebar.header("Search controls")
    query = st.sidebar.text_input("Search query", value="Etruria").strip() or "Etruria"
    page_size = st.sidebar.slider("Page size", min_value=5, max_value=100, value=45)
    images_only = st.sidebar.checkbox("Only records with images", value=False)

    st.sidebar.header("Local date filter")
    made_after_year = int(
        st.sidebar.number_input("Made after year", value=1600, step=1)
    )
    made_before_year = int(
        st.sidebar.number_input("Made before year", value=1900, step=1)
    )
    strict_date_filtering = st.sidebar.checkbox(
        "Strict date filtering",
        value=False,
        help="When off, records with dates that cannot be parsed are kept.",
    )
    fallback_only = st.sidebar.checkbox("Use fallback sample data only", value=False)

    if made_after_year > made_before_year:
        st.sidebar.warning(
            "Made after year is later than made before year; the app will swap "
            "them for filtering."
        )
        made_after_year, made_before_year = made_before_year, made_after_year

    api_url = build_api_url(query, page_size, images_only)
    source_label = "Using fallback sample data"
    warning_message = ""

    if fallback_only:
        raw_df = load_fallback_records()
    else:
        try:
            raw_df, api_url, missing_columns = load_live_records(
                query,
                page_size,
                images_only,
            )
            if missing_columns:
                missing_text = ", ".join(missing_columns)
                raise ValueError(
                    "The live CSV response did not include expected columns: "
                    f"{missing_text}"
                )
            if not has_usable_rows(raw_df):
                raise ValueError("The live CSV response returned no usable rows.")
            source_label = "Using live V&A API data"
        except Exception as error:
            warning_message = (
                "Live V&A API data could not be used. "
                f"{error} Loading fallback sample data instead."
            )
            raw_df = load_fallback_records()

    if warning_message:
        st.warning(warning_message)

    if source_label == "Using live V&A API data":
        st.success(source_label)
    else:
        st.info(source_label)
        st.warning(
            "Fallback sample rows are illustrative and not authoritative V&A "
            "records."
        )

    with st.expander("API request"):
        st.code(api_url, language="text")
        if fallback_only:
            st.caption(
                "No live API request was made because fallback sample data is "
                "selected."
            )

    prepared_df = ensure_expected_columns(raw_df)
    filtered_df = filter_by_date_range(
        prepared_df,
        made_after_year=made_after_year,
        made_before_year=made_before_year,
        strict=strict_date_filtering,
    )
    enriched_df = enrich_records(filtered_df)

    render_summary(enriched_df)

    st.subheader("Object records")
    if enriched_df.empty:
        st.warning(
            "No records match the current filters. Try widening the date range "
            "or turning off strict date filtering."
        )
    else:
        visible_table = enriched_df[DISPLAY_COLUMNS].copy()
        st.dataframe(
            visible_table,
            hide_index=True,
            use_container_width=True,
            column_config={
                "object_page": st.column_config.LinkColumn(
                    "object_page",
                    display_text="V&A object page",
                )
            },
        )

        st.download_button(
            label="Download enriched CSV",
            data=visible_table.to_csv(index=False).encode("utf-8"),
            file_name="invisible_hands_triage_export.csv",
            mime="text/csv",
        )

    render_thumbnails(enriched_df)

    with st.expander("How to read this prototype"):
        st.markdown(
            """
1. Search V&A object records.
2. Inspect maker, maker role, place, date, material, and technique fields.
3. Use the archival tractability score to identify records worth follow-up.
4. Treat the score as a research-triage device, not as evidence of migrant identity.
5. Confirm any historical claim through external archives.
"""
        )

    with st.expander("Methodological caution"):
        st.markdown(
            """
- The score is archival tractability, not migrant likelihood.
- The app separates catalogue-supported clues, research prompts, and evidence gaps.
- No claim about migrant labour should be made from catalogue metadata alone.
- Museum catalogue data can guide archival questioning but cannot replace historical proof.
"""
        )

    with st.expander("Deployment note"):
        st.markdown(
            """
- The app can be deployed on Streamlit Community Cloud from GitHub.
- Entrypoint: app.py.
- No credentials are required.
- The app includes fallback sample data so the interface still works if the live API is unavailable.
"""
        )


if __name__ == "__main__":
    main()

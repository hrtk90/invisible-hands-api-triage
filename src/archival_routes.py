"""Transparent archival next-step recommendations."""

from __future__ import annotations

from src.utils import has_value, safe_text


CAUTION = "Do not infer migrant status from this catalogue record alone."


def recommend_next_steps(row) -> str:
    """Recommend archival follow-up routes from visible catalogue fields."""
    maker = safe_text(row.get("_primaryMaker__name", ""))
    association = safe_text(row.get("_primaryMaker__association", ""))
    place = safe_text(row.get("_primaryPlace", ""))
    material = safe_text(row.get("_sampleMaterial", ""))
    technique = safe_text(row.get("_sampleTechnique", ""))

    recommendations = []

    if has_value(maker):
        recommendations.append(
            "Prosopographical follow-up: check maker biographies, "
            "apprenticeship records, business records, and livery or company "
            "records where relevant."
        )

    if has_value(association):
        recommendations.append(
            "Role-term follow-up: check how this maker association is used in "
            "V&A object files, departmental card indexes, and related catalogue "
            "records."
        )

    if has_value(place):
        recommendations.append(
            "Place-based follow-up: research production or circulation context, "
            "local and civic records, and mapping only where evidence supports it."
        )

    maker_lower = maker.lower()
    if "wedgwood" in maker_lower or "etruria" in maker_lower:
        recommendations.append(
            "Wedgwood-related follow-up: check business archives, orders, "
            "ledgers, correspondence, and manufactory records where available."
        )

    if (has_value(material) or has_value(technique)) and not has_value(maker):
        recommendations.append(
            "Object-led analysis: use material and technique evidence to examine "
            "production process, divided labour, and technical attribution."
        )

    visible_count = sum(
        has_value(row.get(field, ""))
        for field in [
            "objectType",
            "_primaryTitle",
            "_primaryPlace",
            "_primaryMaker__name",
            "_primaryMaker__association",
            "_primaryDate",
            "_sampleMaterial",
            "_sampleTechnique",
            "_primaryImageId",
        ]
    )
    if visible_count <= 2:
        recommendations.append(
            "Metadata-thin record: check departmental card indexes, object files, "
            "and cataloguing history before making interpretive claims."
        )

    if not recommendations:
        recommendations.append(
            "Check object files, departmental indexes, related records, and "
            "cataloguing history before making interpretive claims."
        )

    recommendations.append(CAUTION)
    return " ".join(recommendations)

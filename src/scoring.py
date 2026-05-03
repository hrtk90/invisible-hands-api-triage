"""Rule-based archival tractability scoring."""

from __future__ import annotations

from src.utils import has_value


SCORED_FIELDS = [
    ("objectType", "object type"),
    ("_primaryTitle", "title"),
    ("_primaryPlace", "place"),
    ("_primaryMaker__name", "maker name"),
    ("_primaryMaker__association", "maker association"),
    ("_primaryDate", "date"),
    ("_sampleMaterial", "material"),
    ("_sampleTechnique", "technique"),
    ("_primaryImageId", "image id"),
]


def evidence_status_for_score(score: int) -> str:
    """Convert the numeric tractability score into a cautious evidence label."""
    if score >= 7:
        return "High archival tractability — requires archival follow-up"
    if score >= 5:
        return "Catalogue-supported clue"
    if score >= 3:
        return "Low metadata visibility"
    return "Not assessable from catalogue alone"


def score_record(row) -> dict:
    """Score a single catalogue row by visible fields useful for archival triage."""
    present_labels = []
    for field, label in SCORED_FIELDS:
        if has_value(row.get(field, "")):
            present_labels.append(label)

    score = len(present_labels)
    if present_labels:
        reasons = "; ".join(f"{label} present" for label in present_labels)
    else:
        reasons = "No scored catalogue fields present"

    return {
        "archival_tractability_score": score,
        "evidence_status": evidence_status_for_score(score),
        "evidence_reasons": reasons,
    }

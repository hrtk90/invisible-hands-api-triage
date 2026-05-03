from src.scoring import score_record


FORBIDDEN_LANGUAGE = [
    "migrant " + "probability",
    "probably " + "migrant",
    "migrant" + "-made",
    "non" + "-migrant",
    "ethnicity " + "prediction",
]


def test_full_row_gets_high_score():
    row = {
        "objectType": "Teapot",
        "_primaryTitle": "Creamware teapot",
        "_primaryPlace": "Etruria",
        "_primaryMaker__name": "Josiah Wedgwood and Sons",
        "_primaryMaker__association": "maker",
        "_primaryDate": "about 1775",
        "_sampleMaterial": "earthenware",
        "_sampleTechnique": "transfer-printing",
        "_primaryImageId": "SAMPLEIMG001",
    }

    result = score_record(row)

    assert result["archival_tractability_score"] == 9
    assert (
        result["evidence_status"]
        == "High archival tractability — requires archival follow-up"
    )


def test_thin_row_is_not_assessable_from_catalogue_alone():
    row = {
        "objectType": "",
        "_primaryTitle": "",
        "_primaryPlace": "",
        "_primaryMaker__name": "",
        "_primaryMaker__association": "",
        "_primaryDate": "",
        "_sampleMaterial": "",
        "_sampleTechnique": "",
        "_primaryImageId": "",
    }

    result = score_record(row)

    assert result["archival_tractability_score"] == 0
    assert result["evidence_status"] == "Not assessable from catalogue alone"


def test_scoring_never_uses_forbidden_language():
    result = score_record(
        {
            "objectType": "Plate",
            "_primaryTitle": "Illustrative plate",
            "_primaryPlace": "Staffordshire",
        }
    )
    combined_output = " ".join(str(value).lower() for value in result.values())

    for phrase in FORBIDDEN_LANGUAGE:
        assert phrase not in combined_output

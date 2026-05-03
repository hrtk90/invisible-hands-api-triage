from src.archival_routes import CAUTION, recommend_next_steps


def test_maker_present_triggers_prosopographical_recommendation():
    result = recommend_next_steps({"_primaryMaker__name": "Jane Example"})

    assert "Prosopographical follow-up" in result
    assert CAUTION in result


def test_wedgwood_maker_triggers_business_archive_recommendation():
    result = recommend_next_steps({"_primaryMaker__name": "Josiah Wedgwood"})

    assert "business archives" in result
    assert "ledgers" in result
    assert CAUTION in result


def test_material_or_technique_without_maker_triggers_object_led_analysis():
    result = recommend_next_steps(
        {
            "_sampleMaterial": "earthenware",
            "_sampleTechnique": "transfer-printing",
            "_primaryMaker__name": "",
        }
    )

    assert "Object-led analysis" in result
    assert "divided labour" in result
    assert CAUTION in result


def test_every_recommendation_includes_caution():
    rows = [
        {"_primaryMaker__name": "Jane Example"},
        {"_primaryMaker__name": "Josiah Wedgwood"},
        {"_sampleMaterial": "silk", "_primaryMaker__name": ""},
        {},
    ]

    for row in rows:
        assert CAUTION in recommend_next_steps(row)

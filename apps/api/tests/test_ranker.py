from app.services.ranker import RULE_VERSION, _reason_code


def test_ranker_reason_codes():
    assert _reason_code("WASTE", 12.0, 15) == "RANK_WASTE_COST_RATE"
    assert _reason_code("IDLE", 2.0, 5) == "RANK_IDLE_RESIDUAL"
    assert RULE_VERSION.startswith("rules-ranker")


def test_gmm_air_compressor_alias():
    from app.services.gmm_pulse import gmm_machine_id

    assert gmm_machine_id("air_compressor", "Shop compressor") == "compressor_01"
    assert gmm_machine_id("cnc", "CNC 1") is None

from fieldsense.engine.rollup import compute_rollup


def test_rollup_shape():
    field = {
        "n": 100,
        "p": 40,
        "k": 35,
        "ph": 6.7,
        "moisture": 45,
        "rainfall": 120,
        "humidity": 70,
    }
    out = compute_rollup(field, crop_label="rice")
    assert "health_score" in out
    assert out["risk_level"] in {"low", "medium", "high"}
    assert isinstance(out.get("flags"), list)

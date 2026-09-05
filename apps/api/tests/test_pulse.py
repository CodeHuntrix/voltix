from app.services.pulse import classify_current, refine_waste, residual_waste_kw


class _M:
    thr_off = 0.3
    thr_idle = 2.0
    thr_active = 5.0
    baseline_idle_kw = 0.4


def test_classify_off_active():
    m = _M()
    assert classify_current(0.1, m) == "OFF"
    assert classify_current(7.0, m) == "ACTIVE"
    assert classify_current(1.0, m) == "IDLE"


def test_waste_refine():
    m = _M()
    assert refine_waste("IDLE", 0.8, m) == "WASTE"
    assert residual_waste_kw(0.8, "WASTE", m) > 0

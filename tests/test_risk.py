from backend.core.risk import compute_risk

def test_risk_low():
    assert compute_risk(6) == "LOW"

def test_risk_high():
    assert compute_risk(3) == "HIGH"
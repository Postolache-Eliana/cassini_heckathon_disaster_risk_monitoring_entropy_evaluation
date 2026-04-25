def classify_risk(score: float) -> str:
    if score > 0.5:
        return "high"
    elif score > 0.2:
        return "medium"
    else:
        return "low"
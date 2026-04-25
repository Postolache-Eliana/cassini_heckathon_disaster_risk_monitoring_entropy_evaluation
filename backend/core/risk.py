def classify_risk(relative_score: float) -> str:
    """
    Classify risk based on deviation from baseline.
    """
    if relative_score > 0.2:
        return "high"
    elif relative_score > 0.05:
        return "medium"
    else:
        return "low"
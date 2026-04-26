def classify_risk(relative_score: float):
    """
    FIXED RISK CLASSIFICATION

    Now calibrated for REAL entropy-scale outputs (not normalized 0–1).
    """

    abs_score = abs(relative_score)

    # low change
    if abs_score < 2:
        return "low"

    # moderate change
    elif abs_score < 6:
        return "medium"

    # strong change (flood/drought signal candidate)
    else:
        return "high"
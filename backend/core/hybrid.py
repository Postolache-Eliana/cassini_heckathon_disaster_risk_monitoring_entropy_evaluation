def compute_hybrid_score(satellite_score, camera_entropy_change):
    """
    Simple fusion model for demo.
    """

    # normalize camera signal influence
    camera_component = camera_entropy_change * 0.5

    # satellite dominates long-term signal
    satellite_component = satellite_score * 0.7

    return satellite_component + camera_component


def classify_risk(score):
    if score < 0.2:
        return "low"
    elif score < 0.6:
        return "medium"
    else:
        return "high"
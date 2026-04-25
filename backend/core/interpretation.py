def interpret_results(baseline, current, relative, risk):
    # direction
    if relative > 0.02:
        direction = "increase in environmental activity"
    elif relative < -0.02:
        direction = "decrease in environmental activity"
    else:
        direction = "stable conditions"

    # summary
    if risk == "high":
        summary = "Significant environmental anomaly detected"
        confidence = "high anomaly signal"
    elif risk == "medium":
        summary = "Moderate environmental variation detected"
        confidence = "moderate anomaly signal"
    else:
        summary = "Stable environmental conditions detected"
        confidence = "low anomaly signal"

    return {
        "summary": summary,
        "change_direction": direction,
        "confidence": confidence
    }
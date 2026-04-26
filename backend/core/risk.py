def classify_risk(ndvi_series):
    import numpy as np

    ndvi = np.array(ndvi_series)

    mean = np.mean(ndvi)
    trend = np.polyfit(range(len(ndvi)), ndvi, 1)[0]
    variance = np.var(ndvi)

    # -----------------------------
    # EVENT DETECTION RULES
    # -----------------------------

    strong_trend = abs(trend) > 0.05
    unstable = variance > 0.01

    # flood/drought indicator = sustained movement, not noise
    if strong_trend and mean < 0.1:
        return "high"

    if unstable and abs(trend) < 0.03:
        return "medium"

    return "low"
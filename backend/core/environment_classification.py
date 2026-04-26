import numpy as np


def classify_environment(histograms, relative_score):
    """
    Simple flood vs drought classifier using histogram trends.
    """

    if len(histograms) < 2:
        return {
            "environment": "unknown",
            "confidence": "low"
        }

    # Stack histograms into matrix
    matrix = np.array(histograms)

    # Mean histogram over time
    mean_hist = np.mean(matrix, axis=0)

    # Normalize
    mean_hist = mean_hist / (np.sum(mean_hist) + 1e-6)

    bins = len(mean_hist)
    mid = bins // 2

    # Low reflectance (water / dark surfaces proxy)
    low_region = np.sum(mean_hist[:mid])

    # High reflectance (dry / bright surfaces proxy)
    high_region = np.sum(mean_hist[mid:])

    # Variability over time
    temporal_var = np.std(matrix)

    # RULE-BASED CLASSIFICATION
    if low_region > high_region * 1.2 and relative_score > 0.05:
        return {
            "environment": "flood-like conditions",
            "confidence": "medium",
            "signal": "increase in low-reflectance surfaces"
        }

    if high_region > low_region * 1.2 and relative_score > 0.05:
        return {
            "environment": "drought-like conditions",
            "confidence": "medium",
            "signal": "increase in high-reflectance surfaces"
        }

    if relative_score > 0.15:
        return {
            "environment": "general anomaly",
            "confidence": "medium",
            "signal": "high environmental change detected"
        }

    return {
        "environment": "stable conditions",
        "confidence": "low",
        "signal": "no significant spectral shift"
    }
import numpy as np


# =================================================
# NORMALIZATION HELPERS
# =================================================
def normalize(x, min_val, max_val):

    if max_val - min_val == 0:
        return 0.0

    return (x - min_val) / (max_val - min_val)


# =================================================
# SATELLITE SCORE (KEEP SIMPLE)
# =================================================
def satellite_score(ndvi_series):

    if not ndvi_series:
        return 0.0

    arr = np.array(ndvi_series, dtype=float)

    return float(abs(np.mean(arr) - arr[-1]))


# =================================================
# CAMERA SCORE (ENTROPY-BASED)
# =================================================
def camera_score(camera_features):

    entropy = camera_features.get("entropy", 0.0)
    edges = camera_features.get("edge_density", 0.0)

    entropy_n = normalize(entropy, 0.5, 7.0)
    edges_n = normalize(edges, 0.0, 0.3)

    return float(0.6 * entropy_n + 0.4 * edges_n)


# =================================================
# FINAL FUSION MODEL (CORE OF SYSTEM)
# =================================================
def fused_score(ndvi_series, camera_features):

    sat = satellite_score(ndvi_series)
    cam = camera_score(camera_features)

    # satellite is more reliable → higher weight
    final = 0.75 * sat + 0.25 * cam

    if final < 0.15:
        risk = "low"
    elif final < 0.35:
        risk = "medium"
    else:
        risk = "high"

    return {
        "satellite_score": float(sat),
        "camera_score": float(cam),
        "final_score": float(final),
        "risk": risk
    }
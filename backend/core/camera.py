import cv2
import numpy as np


# =================================================
# IMAGE ENTROPY (CORE SIGNAL)
# =================================================
def image_entropy(image: np.ndarray) -> float:
    """
    Shannon entropy of grayscale image.
    Higher = more texture / activity.
    """

    if image is None:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel()

    if hist.sum() == 0:
        return 0.0

    prob = hist / hist.sum()
    prob = prob[prob > 0]

    return float(-np.sum(prob * np.log2(prob)))


# =================================================
# EDGE DENSITY (STRUCTURE SIGNAL)
# =================================================
def edge_density(image: np.ndarray) -> float:

    if image is None:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    return float(np.mean(edges > 0))


# =================================================
# MAIN CAMERA ANALYZER
# =================================================
def analyze_frame(image_path: str):

    img = cv2.imread(image_path)

    if img is None:
        return {
            "entropy": 0.0,
            "edge_density": 0.0
        }

    entropy = image_entropy(img)
    edges = edge_density(img)

    return {
        "entropy": entropy,
        "edge_density": edges
    }
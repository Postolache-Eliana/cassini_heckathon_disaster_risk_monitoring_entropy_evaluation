import cv2
import numpy as np


# ENTROPY
def image_entropy(image: np.ndarray):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel()

    if hist.sum() == 0:
        return 0.0

    prob = hist / hist.sum()
    prob = prob[prob > 0]

    return float(-np.sum(prob * np.log2(prob)))


# EDGE DENSITY
def edge_density(image: np.ndarray):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    return float(np.mean(edges > 0))


# MAIN ANALYZER
def analyze_frame(image_path: str):

    img = cv2.imread(image_path)

    if img is None:
        return {
            "entropy": 0.0,
            "edge_density": 0.0
        }

    return {
        "entropy": image_entropy(img),
        "edge_density": edge_density(img)
    }
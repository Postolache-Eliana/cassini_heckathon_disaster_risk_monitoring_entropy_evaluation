import cv2
import numpy as np


def image_entropy(image):
    """
    Proper Shannon entropy for grayscale image.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel()

    prob = hist / np.sum(hist + 1e-6)

    prob = prob[prob > 0]

    entropy = -np.sum(prob * np.log2(prob))

    return float(entropy)


def frame_change_entropy(img1, img2):
    """
    Measures change between two frames.
    """

    e1 = image_entropy(img1)
    e2 = image_entropy(img2)

    return abs(e2 - e1)
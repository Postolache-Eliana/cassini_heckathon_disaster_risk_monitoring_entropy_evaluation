import numpy as np

def compute_entropy(image):
    hist = np.histogram(image, bins = 256, range = (0, 256))[0]
    prob = hist / np.sum(hist)
    prob = prob[prob > 0]

    return -np.sum(prob * np.log2(prob))
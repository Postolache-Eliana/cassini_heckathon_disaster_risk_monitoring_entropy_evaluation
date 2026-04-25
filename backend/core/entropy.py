import numpy as np


def compute_histogram(image, bins=32):
    hist, _ = np.histogram(image.flatten(), bins=bins, range=(0, 255))
    return hist


def build_time_matrix(histograms):
    return np.array(histograms)


def matrix_to_point_cloud(matrix):
    points = []

    for t in range(matrix.shape[0]):
        for b in range(matrix.shape[1]):
            freq = matrix[t, b]
            points.append([t, b, freq])

    return np.array(points)


def compute_delta_cloud(points, bias=1.0):
    deltas = []

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]

        L = np.sqrt(dx**2 + dy**2 + dz**2) + 1e-6
        delta = bias / L

        deltas.append([p1[0], p1[1], delta])

    return np.array(deltas)


def compute_change_score(delta_cloud):
    if len(delta_cloud) == 0:
        return 0.0
    return float(np.mean(delta_cloud[:, 2]))
import numpy as np


def normalize(hist):
    hist = np.array(hist, dtype=float)
    s = np.sum(hist)
    return hist / s if s > 0 else hist


def detect_anomaly_map(hist):
    """
    Returns per-bin anomaly strength using z-score.
    """
    hist = np.array(hist)

    mean = np.mean(hist)
    std = np.std(hist) + 1e-6

    return np.abs(hist - mean) / std


def cluster_anomalies(anomaly_map, threshold=2.0):
    """
    Groups adjacent anomalous bins into "events".
    """
    clusters = []
    current = []

    for i, val in enumerate(anomaly_map):

        if val > threshold:
            current.append(val)
        else:
            if current:
                clusters.append(current)
                current = []

    if current:
        clusters.append(current)

    return clusters


def build_time_matrix(histograms):
    return np.array([normalize(h) for h in histograms])


def matrix_to_point_cloud(matrix):
    points = []

    for t in range(matrix.shape[0]):

        anomaly_map = detect_anomaly_map(matrix[t])
        clusters = cluster_anomalies(anomaly_map)

        # 🔥 cluster-level representation (not raw bins anymore)
        cluster_strength = [np.mean(c) for c in clusters] if clusters else [0.0]

        for c in cluster_strength:
            points.append([t, len(cluster_strength), c])

    return np.array(points)


def compute_delta_cloud(points):
    deltas = []

    for i in range(1, len(points)):
        deltas.append(points[i] - points[i - 1])

    return np.array(deltas)


def compute_change_score(delta_cloud):
    if len(delta_cloud) == 0:
        return 0.0

    arr = np.array(delta_cloud)

    magnitudes = np.linalg.norm(arr, axis=1)

    # 🔥 event-based scoring (clusters, not bins)
    mean = np.mean(magnitudes)
    peak = np.max(magnitudes)

    return float(0.4 * mean + 0.6 * peak)
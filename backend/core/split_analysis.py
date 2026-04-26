#TO DELETE

def compute_baseline_and_current(histograms, split_ratio=0.5):
    """
    Split histograms into baseline and current windows.
    """
    n = len(histograms)

    if n < 4:
        return None, None

    split = int(n * split_ratio)

    baseline = histograms[:split]
    current = histograms[split:]

    return baseline, current
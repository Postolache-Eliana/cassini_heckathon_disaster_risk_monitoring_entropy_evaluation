from backend.core.entropy import compute_entropy
import numpy as np

def test_entropy_non_negative():
    img = np.zeros((256, 256))
    assert compute_entropy(img) >= 0
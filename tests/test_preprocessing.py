import numpy as np 
from backend.core.preprocessing import preprocessing

def test_preprocess_shape():
    img = np.zeros((480, 640, 3), dtype = np.uint8)
    out = preprocess(img)
    assert out.shape == out.shape
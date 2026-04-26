from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from enum import Enum
import numpy as np
import cv2
from datetime import datetime

from backend.core.preprocessing import preprocess
from backend.core.satellite import compute_satellite_score
from backend.core.hybrid import classify_risk

router = APIRouter()


class Mode(str, Enum):
    satellite = "satellite"
    image = "image"
    hybrid = "hybrid"


def compute_image_entropy_score(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    hist = hist / (np.sum(hist) + 1e-6)

    hist = hist[hist > 0]
    entropy = -np.sum(hist * np.log2(hist))

    return float(entropy)


@router.post("/analyze")
async def analyze(
    lat: float = Form(...),
    lon: float = Form(...),
    timestamp: str = Form(...),
    mode: Mode = Form(...),
    image: Optional[UploadFile] = File(None)
):

    # ----------------------------
    # Validate timestamp
    # ----------------------------
    try:
        datetime.fromisoformat(timestamp)
    except Exception:
        return {"error": "Invalid timestamp format. Use ISO format."}

    # ----------------------------
    # SATELLITE MODE (NDVI ONLY)
    # ----------------------------
    if mode == Mode.satellite:

        # IMPORTANT:
        # Now returns REAL NDVI-ready histograms internally (no external dependency here)
        from backend.core.satellite import get_satellite_data_series

        data_series = get_satellite_data_series(lat, lon, timestamp)

        score, ndvi_series = compute_satellite_score(data_series)

        risk = classify_risk(score)

        return {
            "mode": "satellite",
            "frames": len(data_series),
            "ndvi_series": ndvi_series,
            "score": round(score, 6),
            "risk": risk,
            "signal": "NDVI temporal analysis"
        }

    # ----------------------------
    # IMAGE MODE
    # ----------------------------
    elif mode == Mode.image:

        if image is None:
            return {"error": "Image required for image mode"}

        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        processed = preprocess(img)

        score = compute_image_entropy_score(processed)
        risk = classify_risk(score)

        return {
            "mode": "image",
            "entropy": round(score, 6),
            "risk": risk,
            "signal": "image entropy analysis"
        }

    # ----------------------------
    # HYBRID MODE
    # ----------------------------
    elif mode == Mode.hybrid:

        if image is None:
            return {"error": "Image required for hybrid mode"}

        from backend.core.satellite import get_satellite_data_series

        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        processed = preprocess(img)

        image_score = compute_image_entropy_score(processed)

        data_series = get_satellite_data_series(lat, lon, timestamp)
        sat_score, ndvi_series = compute_satellite_score(data_series)

        fused_score = (0.7 * sat_score) + (0.3 * image_score)

        risk = classify_risk(fused_score)

        return {
            "mode": "hybrid",
            "ndvi_series": ndvi_series,
            "image_entropy": round(image_score, 6),
            "satellite_score": round(sat_score, 6),
            "fused_score": round(fused_score, 6),
            "risk": risk,
            "signal": "NDVI + image entropy fusion"
        }

    else:
        return {"error": "Invalid mode selected"}
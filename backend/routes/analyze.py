from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from enum import Enum
import numpy as np
import cv2
from datetime import datetime

from backend.core.preprocessing import preprocess
from backend.core.entropy import (
    build_time_matrix,
    matrix_to_point_cloud,
    compute_delta_cloud,
    compute_change_score
)
from backend.core.risk import classify_risk
from backend.core.satellite import get_satellite_histograms

router = APIRouter()


# ------------------------
# MODE ENUM (DROPDOWN)
# ------------------------
class Mode(str, Enum):
    satellite = "satellite"
    image = "image"
    hybrid = "hybrid"


@router.post("/analyze")
async def analyze(
    lat: float = Form(...),
    lon: float = Form(...),
    timestamp: str = Form(...),
    mode: Mode = Form(...),  # ✅ NOW DROPDOWN
    image: Optional[UploadFile] = File(None)
):
    # ------------------------
    # VALIDATION
    # ------------------------
    if not (-90 <= lat <= 90):
        return {"error": "Invalid latitude"}

    if not (-180 <= lon <= 180):
        return {"error": "Invalid longitude"}

    try:
        datetime.fromisoformat(timestamp)
    except Exception:
        return {"error": "Invalid timestamp"}

    # ------------------------
    # SATELLITE MODE
    # ------------------------
    if mode == Mode.satellite:
        histograms = get_satellite_histograms(
            lat,
            lon,
            "2023-01-01",
            "2025-01-01"
        )

        if len(histograms) < 2:
            return {"error": "Not enough satellite data"}

        matrix = build_time_matrix(histograms)
        points = matrix_to_point_cloud(matrix)
        delta = compute_delta_cloud(points)
        score = compute_change_score(delta)

        return {
            "mode": "satellite",
            "frames": len(histograms),
            "score": score,
            "risk": classify_risk(score)
        }

    # ------------------------
    # IMAGE MODE
    # ------------------------
    if mode == Mode.image:
        if image is None:
            return {"error": "Image required for image mode"}

        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        processed = preprocess(img)
        hist = np.histogram(processed.flatten(), bins=32)[0]

        # minimal time-series
        histograms = [hist, hist]

        matrix = build_time_matrix(histograms)
        points = matrix_to_point_cloud(matrix)
        delta = compute_delta_cloud(points)
        score = compute_change_score(delta)

        return {
            "mode": "image",
            "frames": len(histograms),
            "score": score,
            "risk": classify_risk(score)
        }

    # ------------------------
    # HYBRID MODE
    # ------------------------
    if mode == Mode.hybrid:
        if image is None:
            return {"error": "Image required for hybrid mode"}

        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        processed = preprocess(img)
        hist = np.histogram(processed.flatten(), bins=32)[0]

        sat_hist = get_satellite_histograms(
            lat,
            lon,
            "2023-01-01",
            "2025-01-01"
        )

        all_histograms = sat_hist + [hist]

        if len(all_histograms) < 2:
            return {"error": "Not enough data"}

        matrix = build_time_matrix(all_histograms)
        points = matrix_to_point_cloud(matrix)
        delta = compute_delta_cloud(points)
        score = compute_change_score(delta)

        return {
            "mode": "hybrid",
            "frames": len(all_histograms),
            "score": score,
            "risk": classify_risk(score)
        }
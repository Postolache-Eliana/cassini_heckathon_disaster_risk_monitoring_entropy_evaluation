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
from backend.core.interpretation import interpret_results
from backend.core.environment_classification import classify_environment
from backend.core.timeseries import build_time_range_series
from backend.core.satellite import get_satellite_histograms

router = APIRouter()


class Mode(str, Enum):
    satellite = "satellite"
    image = "image"
    hybrid = "hybrid"


@router.post("/analyze")
async def analyze(
    lat: float = Form(...),
    lon: float = Form(...),
    timestamp: str = Form(...),
    mode: Mode = Form(...),
    image: Optional[UploadFile] = File(None)
):

    # ------------------------
    # VALIDATION
    # ------------------------
    try:
        datetime.fromisoformat(timestamp)
    except Exception:
        return {"error": "Invalid timestamp format"}

    # ------------------------
    # TIME SERIES
    # ------------------------
    windows = build_time_range_series(timestamp)

    # ------------------------
    # DATA ACQUISITION
    # ------------------------
    if mode == Mode.satellite:
        histograms = get_satellite_histograms(lat, lon, windows)

    elif mode == Mode.image:
        if image is None:
            return {"error": "Image required"}

        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        processed = preprocess(img)
        hist = np.histogram(processed.flatten(), bins=32)[0]

        histograms = [hist for _ in windows]

    elif mode == Mode.hybrid:
        if image is None:
            return {"error": "Image required"}

        contents = await image.read()
        np_arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        processed = preprocess(img)
        hist = np.histogram(processed.flatten(), bins=32)[0]

        sat = get_satellite_histograms(lat, lon, windows)

        histograms = sat + [hist]

    else:
        return {"error": "Invalid mode"}

    # ------------------------
    # ENSURE ENOUGH DATA
    # ------------------------
    if len(histograms) < 4:
        return {
            "error": "Insufficient satellite data",
            "frames": len(histograms)
        }

    # ------------------------
    # IMPORTANT FIX: asymmetric split
    # ------------------------
    split = max(2, int(len(histograms) * 0.7))

    baseline_hist = histograms[:split]
    current_hist = histograms[split:]

    # ------------------------
    # ENTROPY PIPELINE
    # ------------------------
    matrix_b = build_time_matrix(baseline_hist)
    points_b = matrix_to_point_cloud(matrix_b)
    delta_b = compute_delta_cloud(points_b)
    baseline_score = compute_change_score(delta_b)

    matrix_c = build_time_matrix(current_hist)
    points_c = matrix_to_point_cloud(matrix_c)
    delta_c = compute_delta_cloud(points_c)
    current_score = compute_change_score(delta_c)

    print("BASELINE RAW SAMPLE:", np.array(baseline_hist)[:2])
    print("CURRENT RAW SAMPLE:", np.array(current_hist)[:2])

    relative_score = current_score - baseline_score
    risk = classify_risk(relative_score)

    interpretation = interpret_results(
        baseline_score,
        current_score,
        relative_score,
        risk
    )

    env = classify_environment(histograms, relative_score)

    return {
        "mode": mode,
        "frames": len(histograms),

        "baseline_score": round(baseline_score, 6),
        "current_score": round(current_score, 6),
        "relative_score": round(relative_score, 6),

        "risk": risk,

        **interpretation,
        **env
    }
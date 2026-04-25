from fastapi import APIRouter, UploadFile, File, Form
import numpy as np
import cv2
import datetime

from backend.core.preprocessing import preprocess
from backend.core.entropy import (
    compute_histogram,
    build_time_matrix,
    matrix_to_point_cloud,
    compute_delta_cloud,
    compute_change_score
)
from backend.core.satellite import get_satellite_histograms


router = APIRouter()


def classify_risk(score):
    if score > 0.5:
        return "HIGH"
    elif score > 0.2:
        return "MEDIUM"
    return "LOW"


@router.post("/analyze")
async def analyze(
    lat: float = Form(...),
    lon: float = Form(...),
    timestamp: str = Form(...),
    image: UploadFile = File(...)
):

    if not (-90 <= lat <= 90):
        return {"error": "Invalid latitude"}

    if not (-180 <= lon <= 180):
        return {"error": "Invalid longitude"}

    try:
        datetime.datetime.fromisoformat(timestamp)
    except:
        return {"error": "Invalid timestamp"}

    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Invalid image"}

    processed = preprocess(img)
    drone_hist = compute_histogram(processed)

    sat_histograms = get_satellite_histograms(
        lat,
        lon,
        "2024-01-01",
        "2024-01-05"
    )

    # fallback safety
    if len(sat_histograms) == 0:
        sat_histograms = [drone_hist]

    all_histograms = sat_histograms + [drone_hist]

    matrix = build_time_matrix(all_histograms)
    points = matrix_to_point_cloud(matrix)
    delta_cloud = compute_delta_cloud(points)
    score = compute_change_score(delta_cloud)

    return {
        "lat": lat,
        "lon": lon,
        "frames_used": len(all_histograms),
        "change_score": float(score),
        "risk": classify_risk(score)
    }
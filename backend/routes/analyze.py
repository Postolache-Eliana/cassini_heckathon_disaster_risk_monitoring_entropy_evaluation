from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os

from backend.core.satellite import get_satellite_data_series
from backend.core.camera import analyze_frame
from backend.core.fusion import fused_score

router = APIRouter()


class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    timestamp: str
    image_path: Optional[str] = None


@router.post("/analyze")
async def analyze(payload: AnalyzeRequest):

    # SATELLITE
    ndvi_series = get_satellite_data_series(
        payload.lat,
        payload.lon,
        payload.timestamp
    )

    if ndvi_series is None:
        ndvi_series = []

    # CAMERA (SAFE)
    camera_features = {
        "entropy": 0.0,
        "edge_density": 0.0
    }

    if payload.image_path and os.path.exists(payload.image_path):
        camera_features = analyze_frame(payload.image_path)
    else:
        print("[CAMERA SKIPPED - INVALID PATH]")

    # FUSION
    result = fused_score(ndvi_series, camera_features)

    return {
        "mode": "fusion",
        "frames": len(ndvi_series),
        "ndvi_series": ndvi_series,
        "camera": camera_features,
        **result
    }
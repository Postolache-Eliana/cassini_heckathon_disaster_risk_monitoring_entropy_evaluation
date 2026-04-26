from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import os

from backend.core.satellite import get_satellite_data_series
from backend.core.camera import analyze_frame
from backend.core.fusion import fused_score

router = APIRouter()


# MODE ENUM 
class Mode(str, Enum):
    satellite = "satellite"
    camera = "camera"
    fusion = "fusion"


# REQUEST MODEL
class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    timestamp: str
    image_path: Optional[str] = None
    mode: Mode = Mode.fusion


# MAIN ENDPOINT
@router.post("/analyze")
async def analyze(payload: AnalyzeRequest):

    # 1. SATELLITE (DEFAULT)
    ndvi_series = get_satellite_data_series(
        payload.lat,
        payload.lon,
        payload.timestamp
    )

    if ndvi_series is None:
        ndvi_series = []

    # 2. CAMERA (DEFAULT SAFE)
    camera_features = {
        "entropy": 0.0,
        "edge_density": 0.0
    }

    if payload.image_path and os.path.exists(payload.image_path):
        camera_features = analyze_frame(payload.image_path)
    else:
        print("[CAMERA SKIPPED - INVALID PATH]")

    # 3. MODE SWITCHING LOGIC
    if payload.mode == Mode.satellite:
        # Ignore camera completely
        camera_features = {
            "entropy": 0.0,
            "edge_density": 0.0
        }

    elif payload.mode == Mode.camera:
        # Ignore satellite completely
        ndvi_series = []

    # fusion mode → uses both (default behavior)

    # 4. FUSION
    result = fused_score(ndvi_series, camera_features)

    # 5. RESPONSE
    return {
        "mode": payload.mode,
        "frames": len(ndvi_series),

        "ndvi_series": ndvi_series,
        "camera": camera_features,

        "satellite_score": result["satellite_score"],
        "camera_score": result["camera_score"],
        "final_score": result["final_score"],
        "risk": result["risk"]
    }
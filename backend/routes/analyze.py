from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.core.satellite import get_satellite_data_series
from backend.core.camera import analyze_frame
from backend.core.fusion import fused_score

router = APIRouter()


# =================================================
# REQUEST MODEL
# =================================================
class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    timestamp: str
    image_path: Optional[str] = None


# =================================================
# MAIN ENDPOINT
# =================================================
@router.post("/analyze")
async def analyze(payload: AnalyzeRequest):

    # -----------------------------
    # 1. SATELLITE NDVI PIPELINE
    # -----------------------------
    ndvi_series = get_satellite_data_series(
        payload.lat,
        payload.lon,
        payload.timestamp
    )

    if ndvi_series is None:
        ndvi_series = []

    # -----------------------------
    # 2. CAMERA PIPELINE (OPTIONAL)
    # -----------------------------
    camera_features = {
        "entropy": 0.0,
        "edge_density": 0.0
    }

    if payload.image_path:
        camera_features = analyze_frame(payload.image_path)

    # -----------------------------
    # 3. FUSION MODEL
    # -----------------------------
    result = fused_score(ndvi_series, camera_features)

    # -----------------------------
    # 4. RESPONSE FORMAT
    # -----------------------------
    return {
        "mode": "fusion",
        "frames": len(ndvi_series),

        "ndvi_series": ndvi_series,
        "camera": camera_features,

        "satellite_score": result["satellite_score"],
        "camera_score": result["camera_score"],
        "final_score": result["final_score"],
        "risk": result["risk"]
    }
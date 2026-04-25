from fastapi import APIRouter, UploadFile, File, Form 
import numpy as np 
import cv2
import os 
from datetime import datetime

from backend.core.preprocessing import preprocess
from backend.core.entropy import compute_entropy
from backend.core.risk import compute_risk 
from backend.state import latest_result

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok = True)

def validate_coordinates(lat, lon):
    if not (-90 <= lat <= 90):
        return "Invalid latitude"
    if not (-180 <= lon <= 180):
        return "Invalid longitude"
    return None

def validate_timestamp(timestamp):
    if not timestamp or len(timestamp.strip()) == 0:
        return "Missing Timestamp"
    return None

@router.post(
    "/analyze",
    summary="Analyze drone image",
    description="Uploads a drone image with GPS metadata, preprocesses it, computes Shannon entropy, and returns a disaster risk level."
)
async def analyze(
    lat: float = Form(..., description="Latitude of the drone capture point. Must be between -90 and 90.", examples=[44.4268]),
    lon: float = Form(..., description="Longitude of the drone capture point. Must be between -180 and 180.", examples=[26.1025]),
    timestamp: str = Form(..., description="Capture timestamp in ISO format.", examples=["2026-04-25T14:30:00Z"]),
    file: UploadFile = File(..., description="Drone image captured by the ESP32CAM module.")
    #device_id: str = Form("drone_01")
    #alt: float = Form(0)
):
    try:
        #validation
        coord_error = validate_coordinates(lat, lon)
        if coord_error:
            return {"error": coord_error}

        time_error = validate_timestamp(timestamp)
        if time_error:
            return {"error": time_error}

        #image decoding
        image_bytes = await file.read()
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return {"error": "Invalid Image"}

        #saving image
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)

        #processing image
        processed = preprocess(img)
        entropy_val = compute_entropy(processed)
        risk = compute_risk(entropy_val)

        result = {
            "lat": lat,
            "lon": lon,
            "timestamp": timestamp,
            "entropy": float(entropy_val),
            "risk": risk,
            "file": filename
        }

        #save state
        latest_result.clear()
        latest_result.update(result)

        return result

    except Exception as e:
        return {"error": str(e)}


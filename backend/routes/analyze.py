from fastapi import APIRouter, UploadFile, File, Form 
import numpy as np 
import cv2
import os 
from datetime import datetime

from core.preprocessing import preprocess
from core.entropy import compute_entropy
from core.risk import compute_risk 
from state import latest_result

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

@router.post("/analyze")
async def analyze(
    lat: float = Form(...),
    lon: float = Form(...),
    timestamp: str = Form(...),
    file: UploadFile = File(...)
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
        np_arr
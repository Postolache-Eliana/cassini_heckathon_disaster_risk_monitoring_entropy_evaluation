from fastapi import FastAPI, File, Form, UploadFile
import numpy as np
import cv2
import os
from datetime import datetime

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok = True)

@app.post("/analyze")
async def analyze(
    lat: float = Form(...),
    lon: float = Form(...),
    timestamp: str = Form(...),
    file: UploadFile = File(...)
):

    try:
        image_bytes = await file.read()
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return {"error": "Invalid Image"}

        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)

        cv2.imwrite(filepath, img)

        print (f"Received image at {lat}, {lon} time {timestamp}")

        return {
            "status": "success",
            "filename": filename,
            "lat": lat,
            "lon": lon
        }

    except Exception as e:
        return {"error": str(e)}
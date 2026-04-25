import requests
import numpy as np
import cv2

from backend.core.auth import get_access_token

STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac"

def search_sentinel(lat, lon, start_date, end_date):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    bbox = [lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01]

    params = {
        "collections": ["sentinel-2-l2a"],
        "bbox": bbox,
        "datetime": f"{start_date}/{end_date}",
        "limit": 5
    }

    response = requests.get(
        f"{STAC_URL}/search",
        headers=headers,
        params=params
    )

    response.raise_for_status()
    return response.json().get("features", [])

def download_preview(feature):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    assets = feature.get("assets", {})
    url = assets.get("visual", {}).get("href")

    if not url:
        return None

    response = requests.get(url, headers=headers)

    img_array = np.frombuffer(response.content, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    return img

def image_to_histogram(image, bins=32):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist, _ = np.histogram(gray.flatten(), bins=bins, range=(0, 255))
    return hist

def get_satellite_histograms(lat, lon, start_date, end_date):
    features = search_sentinel(lat, lon, start_date, end_date)

    histograms = []

    for feature in features:
        img = download_preview(feature)
        if img is None:
            continue

        hist = image_to_histogram(img)
        histograms.append(hist)

    return histograms
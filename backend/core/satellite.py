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

    # progressively expanding search areas
    search_steps = [0.05, 0.1, 0.2]  # ~5km, 10km, 20km

    datetime_range = (
        f"{start_date}T00:00:00Z/"
        f"{end_date}T23:59:59Z"
    )

    for step in search_steps:
        bbox = [
            lon - step,
            lat - step,
            lon + step,
            lat + step
        ]

        bbox_str = ",".join(map(str, bbox))

        params = {
            "collections": "sentinel-2-l2a",
            "bbox": bbox_str,
            "datetime": datetime_range,
            "limit": 10
        }

        response = requests.get(
            f"{STAC_URL}/search",
            headers=headers,
            params=params
        )

        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])

        print(f"[STAC] bbox={step} → features={len(features)}")

        if features:
            return features

    return []


def download_preview(feature):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    assets = feature.get("assets", {})

    url = (
        assets.get("visual", {}).get("href")
        or assets.get("thumbnail", {}).get("href")
        or assets.get("rendered_preview", {}).get("href")
    )

    if not url:
        print("[WARN] No usable asset found")
        return None

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("[WARN] Download failed:", response.status_code)
        return None

    img_array = np.frombuffer(response.content, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    return img

# ----------------------------
# IMAGE → HISTOGRAM
# ----------------------------
def image_to_histogram(image, bins=32):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist, _ = np.histogram(gray.flatten(), bins=bins, range=(0, 255))
    return hist


# ----------------------------
# FULL PIPELINE
# ----------------------------
def get_satellite_histograms(lat, lon, start_date, end_date):
    features = search_sentinel(lat, lon, start_date, end_date)

    print(f"[SATELLITE] total features: {len(features)}")

    histograms = []

    for feature in features:
        img = download_preview(feature)
        if img is None:
            continue

        histograms.append(image_to_histogram(img))

    return histograms
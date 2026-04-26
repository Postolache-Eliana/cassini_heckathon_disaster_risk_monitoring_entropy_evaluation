#TO DELETE
import os
import requests
import numpy as np
import rasterio
import tempfile


# -------------------------------------------------
# CDSE AUTH CONFIG
# -------------------------------------------------
CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"


# -------------------------------------------------
# AUTH TOKEN CACHE
# -------------------------------------------------
_access_token = None


def get_token():
    """
    OAuth2 client credentials flow (CDSE official method)
    """

    global _access_token

    if _access_token:
        return _access_token

    data = {
        "client_id": CDSE_CLIENT_ID,
        "client_secret": CDSE_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    r = requests.post(TOKEN_URL, data=data)

    if r.status_code != 200:
        raise Exception(f"Auth failed: {r.text}")

    _access_token = r.json()["access_token"]
    return _access_token


def auth_headers():
    return {
        "Authorization": f"Bearer {get_token()}"
    }


# -------------------------------------------------
# TIME WINDOWS
# -------------------------------------------------
from datetime import datetime, timedelta


def build_windows(timestamp: str, days=5, steps=6):
    base = datetime.fromisoformat(timestamp.replace("Z", ""))

    return [
        (
            (base + timedelta(days=i * days)).isoformat(),
            (base + timedelta(days=i * days + days)).isoformat()
        )
        for i in range(steps)
    ]


# -------------------------------------------------
# STAC QUERY (REAL)
# -------------------------------------------------
def stac_search(bbox, start, end):
    payload = {
        "collections": "sentinel-2-l2a",
        "bbox": ",".join(map(str, bbox)),
        "datetime": f"{start}/{end}",
        "limit": 1
    }

    r = requests.post(STAC_URL, json=payload, headers=auth_headers())

    if r.status_code != 200:
        return []

    return r.json().get("features", [])


# -------------------------------------------------
# DOWNLOAD ASSET
# -------------------------------------------------
def download_tif(url):
    r = requests.get(url, headers=auth_headers(), stream=True)

    if r.status_code != 200:
        return None

    tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)

    for chunk in r.iter_content(1024 * 1024):
        tmp.write(chunk)

    tmp.close()
    return tmp.name


# -------------------------------------------------
# NDVI FROM REAL PIXELS
# -------------------------------------------------
def compute_ndvi(red_path, nir_path):
    with rasterio.open(red_path) as red_src:
        red = red_src.read(1).astype(float)

    with rasterio.open(nir_path) as nir_src:
        nir = nir_src.read(1).astype(float)

    denom = nir + red
    denom[denom == 0] = np.nan

    ndvi = (nir - red) / denom

    return float(np.nanmean(ndvi))


# -------------------------------------------------
# MAIN NDVI ENGINE
# -------------------------------------------------
def get_satellite_ndvi_series(lat: float, lon: float, timestamp: str):
    """
    REAL Sentinel-2 pixel-level NDVI time series
    """

    bbox = [lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05]
    windows = build_windows(timestamp)

    series = []

    for start, end in windows:

        features = stac_search(bbox, start, end)

        if not features:
            series.append(0.0)
            continue

        item = features[0]
        assets = item.get("assets", {})

        red_url = assets.get("B04", {}).get("href")
        nir_url = assets.get("B08", {}).get("href")

        if not red_url or not nir_url:
            series.append(0.0)
            continue

        red_path = download_tif(red_url)
        nir_path = download_tif(nir_url)

        if not red_path or not nir_path:
            series.append(0.0)
            continue

        try:
            ndvi = compute_ndvi(red_path, nir_path)
            series.append(ndvi)

        except Exception:
            series.append(0.0)

        finally:
            import os
            if red_path and os.path.exists(red_path):
                os.remove(red_path)
            if nir_path and os.path.exists(nir_path):
                os.remove(nir_path)

    return series


# -------------------------------------------------
# DEBUG
# -------------------------------------------------
def debug(lat, lon, timestamp):
    data = get_satellite_ndvi_series(lat, lon, timestamp)
    print("[NDVI SERIES]", data)
    return data
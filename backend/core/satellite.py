import os
import numpy as np
import openeo
import rasterio
from datetime import datetime, timedelta
from pathlib import Path


# =================================================
# CONFIG
# =================================================
OPENEO_URL = "https://openeo.dataspace.copernicus.eu"

CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")


# =================================================
# CONNECTION (FIXED PROVIDER)
# =================================================
def get_connection():
    conn = openeo.connect(OPENEO_URL)

    conn.authenticate_oidc_client_credentials(
        client_id=CDSE_CLIENT_ID,
        client_secret=CDSE_CLIENT_SECRET,
        provider_id="CDSE"
    )

    return conn


# =================================================
# TIME WINDOW
# =================================================
def build_window(timestamp: str):
    base = datetime.fromisoformat(timestamp.replace("Z", ""))
    start = base
    end = base + timedelta(days=5)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# =================================================
# SAFE NDVI ENGINE
# =================================================
def get_satellite_ndvi_series(lat: float, lon: float, timestamp: str):

    try:
        start, end = build_window(timestamp)

        bbox = {
            "west": lon - 0.05,
            "south": lat - 0.05,
            "east": lon + 0.05,
            "north": lat + 0.05
        }

        print("[OPENEO WINDOW]", start, "→", end)

        conn = get_connection()

        # =================================================
        # LOAD SENTINEL-2 L2A
        # =================================================
        cube = conn.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=bbox,
            temporal_extent=[start, end],
            bands=["B04", "B08"]
        )

        # =================================================
        # NDVI
        # =================================================
        ndvi = (cube.band("B08") - cube.band("B04")) / (
            cube.band("B08") + cube.band("B04")
        )

        ndvi = ndvi.mean_time()

        # =================================================
        # EXECUTE JOB
        # =================================================
        job = ndvi.execute_batch()
        results = job.get_results()

        files = results.download_files()

        if not files:
            print("[NO OUTPUT FILES]")
            return []

        values = []

        # =================================================
        # SAFE FILE HANDLING (FIXES PosixPath ERROR)
        # =================================================
        for f in files:
            p = Path(f)

            if p.suffix.lower() not in [".tif", ".tiff"]:
                continue

            try:
                with rasterio.open(str(p)) as src:
                    arr = src.read(1).astype(float)

                    arr = arr[~np.isnan(arr)]

                    if len(arr) > 0:
                        values.append(float(np.mean(arr)))

            except Exception as e:
                print("[FILE READ ERROR]", e)
                continue

        if not values:
            print("[NO VALID NDVI VALUES]")
            return []

        mean_ndvi = float(np.mean(values))

        print("[NDVI RESULT]", mean_ndvi)

        return [mean_ndvi]

    except Exception as e:
        print("[SATELLITE ERROR]", str(e))
        return []


# =================================================
# SCORING
# =================================================
def compute_satellite_score(series):

    try:
        arr = np.array(series, dtype=float)

        if len(arr) == 0:
            return 0.0, []

        score = abs(0.5 - float(np.mean(arr)))

        return float(score), arr.tolist()

    except Exception:
        return 0.0, []


# =================================================
# FASTAPI COMPATIBILITY
# =================================================
get_satellite_data_series = get_satellite_ndvi_series
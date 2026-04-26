import os
import numpy as np
import openeo
from datetime import datetime, timedelta


# CONFIG
OPENEO_URL = "https://openeo.dataspace.copernicus.eu"

CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")


# CONNECTION
def get_connection():
    conn = openeo.connect(OPENEO_URL)

    conn.authenticate_oidc_client_credentials(
        client_id=CDSE_CLIENT_ID,
        client_secret=CDSE_CLIENT_SECRET,
        provider_id="CDSE"
    )

    return conn


# TIME WINDOW
def build_window(timestamp: str):
    base = datetime.fromisoformat(timestamp.replace("Z", ""))

    start = base
    end = base + timedelta(days=5)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# MAIN NDVI ENGINE 
def get_satellite_ndvi_series(lat: float, lon: float, timestamp: str):

    try:
        start, end = build_window(timestamp)

        print("[OPENEO WINDOW]", start, "→", end)

        conn = get_connection()

        bbox = {
            "west": lon - 0.05,
            "south": lat - 0.05,
            "east": lon + 0.05,
            "north": lat + 0.05
        }

        # LOAD SENTINEL-2 L2A
        cube = conn.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=bbox,
            temporal_extent=[start, end],
            bands=["B04", "B08"]
        )

        # NDVI
        ndvi = cube.ndvi(red="B04", nir="B08")

        # temporal aggregation (safe)
        ndvi = ndvi.mean_time()

        # EXECUTE
        job = ndvi.execute_batch()

        result = job.get_results()

        # safer extraction: take first available array
        try:
            array = result.xarray()

            values = array.values.flatten()
            values = values[~np.isnan(values)]

            if len(values) == 0:
                print("[EMPTY NDVI ARRAY]")
                return []

            mean_ndvi = float(np.mean(values))

            print("[NDVI RESULT]", mean_ndvi)

            return [mean_ndvi]

        except Exception as e:
            print("[RESULT PARSE ERROR]", str(e))
            return []

    except Exception as e:
        print("[SATELLITE ERROR]", str(e))
        return []

# SCORING MODEL
def compute_satellite_score(series):

    arr = np.array(series, dtype=float)

    if len(arr) == 0:
        return 0.0, []

    baseline = np.mean(arr)
    current = arr[-1]

    score = abs(current - baseline)

    return float(score), arr.tolist()


# ALIAS FOR BACKWARD COMPATIBILITY (DO NOT DELETE, WILL NOT WORK WITHOUT THIS FOR SOME REASON)
get_satellite_data_series = get_satellite_ndvi_series
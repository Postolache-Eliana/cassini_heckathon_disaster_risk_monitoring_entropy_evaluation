import os
import numpy as np
import openeo
import rasterio
from datetime import datetime, timedelta


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


# NDVI ENGINE (STABLE + FALLBACK)
def get_satellite_data_series(lat: float, lon: float, timestamp: str):

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

        cube = conn.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=bbox,
            temporal_extent=[start, end],
            bands=["B04", "B08"]
        )

        # Correct NDVI
        ndvi = cube.ndvi(red="B04", nir="B08").mean_time()

        job = ndvi.execute_batch()
        result = job.get_results()

        files = result.download_files()

        values = []

        for f in files:
            try:
                with rasterio.open(str(f)) as src:
                    arr = src.read(1).astype(float)
                    arr = arr[~np.isnan(arr)]

                    if len(arr) > 0:
                        values.append(float(np.mean(arr)))

            except Exception as e:
                print("[RASTER READ ERROR]", e)

        # HARD FALLBACK (CRITICAL)
        if not values:
            print("[FALLBACK NDVI USED]")
            return [0.2]

        mean_ndvi = float(np.mean(values))

        print("[NDVI RESULT]", mean_ndvi)

        return [mean_ndvi]

    except Exception as e:
        print("[SATELLITE ERROR]", str(e))
        return [0.2]
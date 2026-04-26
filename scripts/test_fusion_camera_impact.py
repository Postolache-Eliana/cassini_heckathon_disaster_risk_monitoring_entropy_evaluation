import os
from backend.core.satellite import get_satellite_data_series
from backend.core.camera import analyze_frame
from backend.core.fusion import fused_score


def get_image_path(name):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, "uploads", name)


def main():

    lat = 44.4
    lon = 26.1
    timestamp = "2025-07-15T12:00:00Z"

    print("\n[STEP 1] Fetching NDVI...")
    ndvi_series = get_satellite_data_series(lat, lon, timestamp)

    print("[NDVI]", ndvi_series)

    # SCENARIO A: LOW ACTIVITY IMAGE
    img_low = get_image_path("test1.jpeg")

    camera_low = analyze_frame(img_low)

    result_low = fused_score(ndvi_series, camera_low)

    print("\n===== SCENARIO A (LOW ACTIVITY) =====")
    print("Camera:", camera_low)
    print("Final Score:", result_low["final_score"])
    print("Risk:", result_low["risk"])

    # SCENARIO B: HIGH ACTIVITY IMAGE
    img_high = get_image_path("test2.jpg")

    camera_high = analyze_frame(img_high)

    result_high = fused_score(ndvi_series, camera_high)

    print("\n===== SCENARIO B (HIGH ACTIVITY) =====")
    print("Camera:", camera_high)
    print("Final Score:", result_high["final_score"])
    print("Risk:", result_high["risk"])

    # COMPARISON
    print("\n===== DELTA CHECK =====")
    print("Score difference:",
          result_high["final_score"] - result_low["final_score"])


if __name__ == "__main__":
    main()
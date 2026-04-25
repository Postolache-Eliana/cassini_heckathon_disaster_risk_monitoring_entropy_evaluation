print("TEST STARTED")

from backend.core.satellite import get_satellite_histograms


def test_satellite():
    lat = 44.4268
    lon = 26.1025

    histograms = get_satellite_histograms(
        lat,
        lon,
        "2024-01-01",
        "2024-01-05"
    )

    print("Satellite frames:", len(histograms))
    print(histograms)


test_satellite()
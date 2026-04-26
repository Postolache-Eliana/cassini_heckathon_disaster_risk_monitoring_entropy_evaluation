# Satellite NDVI Intelligence Module

This module is part of a geospatial environmental monitoring system that performs **real-time vegetation analysis using Sentinel-2 satellite data via Copernicus Data Space Ecosystem (CDSE) and OpenEO**.

It currently implements a fully working **NDVI time-series extraction + anomaly detection pipeline**.

---

# Features

## Satellite Data Pipeline
- Fetches Sentinel-2 L2A imagery via OpenEO (CDSE backend)
- Extracts spectral bands:
  - B04 (Red)
  - B08 (Near Infrared)
- Computes NDVI:
  
  NDVI = (NIR - RED) / (NIR + RED)

- Builds multi-window temporal NDVI series
- Handles cloud execution via OpenEO batch jobs

---

## Time-Series Analysis
- Generates NDVI history over configurable time windows
- Computes:
  - baseline NDVI (historical mean)
  - current NDVI
  - deviation (z-score)

---

## Risk Scoring Model
A lightweight anomaly detector:

- NDVI drop → drought-like signal
- NDVI spike → flood/vegetation anomaly
- Stable variation → normal conditions

Output:

```json
{
  "score": 0.83,
  "risk": "high",
  "baseline": 0.62,
  "current": 0.41
}
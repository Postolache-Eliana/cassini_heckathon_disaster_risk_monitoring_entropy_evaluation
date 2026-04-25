from fastapi import FastAPI 
from backend.routes.analyze import router as analyze_router
from backend.state import latest_result

app = FastAPI(
    title="Disaster Risk Monitoring API",
    description="Drone and satellite-assisted disaster risk monitoring API using entropy-based image analysis.",
    version="1.0.0"
)

app.include_router(analyze_router)

@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/latest-result")
def get_latest():
    return latest_result if latest_result else {"message": "No Data Yet"}
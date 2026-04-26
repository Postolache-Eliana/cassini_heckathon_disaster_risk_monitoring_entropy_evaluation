from fastapi.testclient import TestClient 
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status.code == 200
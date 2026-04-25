import requests
from backend.core.config import CDSE_CLIENT_ID, CDSE_CLIENT_SECRET

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"


def get_access_token():
    if not CDSE_CLIENT_ID or not CDSE_CLIENT_SECRET:
        raise ValueError("Missing CDSE credentials")

    data = {
        "grant_type": "client_credentials",
        "client_id": CDSE_CLIENT_ID,
        "client_secret": CDSE_CLIENT_SECRET
    }

    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()

    return response.json()["access_token"]
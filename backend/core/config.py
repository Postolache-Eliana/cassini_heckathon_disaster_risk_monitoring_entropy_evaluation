import os
from dotenv import load_dotenv

load_dotenv()

CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")
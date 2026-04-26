import os
from dotenv import load_dotenv

load_dotenv()

# STORED AT OS LEVEL, PATH ~/.bashrc
CDSE_CLIENT_ID = os.getenv("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.getenv("CDSE_CLIENT_SECRET")
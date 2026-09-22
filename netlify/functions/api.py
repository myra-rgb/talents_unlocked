import os
import sys
from pathlib import Path

# Add project root directory to sys.path so modules (main, database) can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mangum import Mangum
from main import app
from database import initialize_database

# Ensure database tables exist in serverless environment
try:
    initialize_database()
except Exception:
    pass

handler = Mangum(app, api_gateway_base_path="/.netlify/functions/api")

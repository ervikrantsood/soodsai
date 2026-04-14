import os
from dotenv import load_dotenv

# Load .env file (works both locally and on Render/Heroku)
load_dotenv()

# ─────────────────────────────────────────
#  API KEYS — Update your keys here
# ─────────────────────────────────────────
# ─────────────────────────────────────────
#  API KEYS — Managed in api_keys.py
# ─────────────────────────────────────────
try:
    from api_keys import KEYS as GEMINI_API_KEYS
except ImportError:
    GEMINI_API_KEYS = [
        os.getenv("GEMINI_API_KEY_1", "AIzaSyB1DYgkyVpQq1WpacpuHTcdRVugzPnoJ3w"),
        os.getenv("GEMINI_API_KEY_2", "AIzaSyBIIKH3hpTF-2wiiyWOb_oZzbmzoi4-iww"),        
        os.getenv("GEMINI_API_KEY_3", "AIzaSyDlKTxrRUaGV9OYV6gYC8SHpfbyOv4byCc"),
        os.getenv("GEMINI_API_KEY_4", "AIzaSyAjLJG1m0Y4LpGep7W3jd-libilm8Y3a1A"),
        os.getenv("GEMINI_API_KEY_5", "AIzaSyABP2-9VZcNbr6UnhDs-dghkdPk2BNkKGY"),
        os.getenv("GEMINI_API_KEY_6", "AIzaSyBo5y2GAPsKR1DSb_CofFI_CspH2SRv2yk")
    ]


# ─────────────────────────────────────────
#  App Settings
# ─────────────────────────────────────────
DEFAULT_TICKER   = "USO"
DEFAULT_LANGUAGE = "Hinglish"
SERVER_PORT      = int(os.getenv("PORT", 5000))

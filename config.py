import os
from dotenv import load_dotenv

# Load .env file (works both locally and on Render/Heroku)
load_dotenv()

# ─────────────────────────────────────────
#  API KEYS — Multi-key support
# ─────────────────────────────────────────
try:
    from api_keys import KEYS as GEMINI_API_KEYS
except ImportError:
    # Fallback to .env or Environment Variables (for Render/Heroku)
    # Expects a comma-separated string of keys
    keys_str = os.getenv("GEMINI_API_KEYS", "")
    GEMINI_API_KEYS = [k.strip() for k in keys_str.split(",") if k.strip()]

# ─────────────────────────────────────────
#  App Settings
# ─────────────────────────────────────────
DEFAULT_TICKER   = "USO"
DEFAULT_LANGUAGE = "Hinglish"
SERVER_PORT      = int(os.getenv("PORT", 5000))

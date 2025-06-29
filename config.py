import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0")) # Optional: for logging to a specific channel

# Log level configuration - default to INFO
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# --- Proxy Configuration ---
# Example: "socks5://user:pass@host:port" or "http://host:port"
PROXY_URL = os.environ.get("PROXY_URL")

PROXY = None
if PROXY_URL:
    from urllib.parse import urlparse
    parsed_proxy = urlparse(PROXY_URL)
    PROXY = {
        "scheme": parsed_proxy.scheme or "http",
        "hostname": parsed_proxy.hostname,
        "port": parsed_proxy.port,
        "username": parsed_proxy.username,
        "password": parsed_proxy.password,
    }
    # Pyrogram expects scheme to be one of "socks4", "socks5", "http"
    # The default http proxy in pyrogram is handled by setting the scheme to "http"
    if PROXY["scheme"] not in ["socks4", "socks5", "http"]:
        # Fallback to http for schemes like https
        PROXY["scheme"] = "http"

if not all([API_ID, API_HASH, BOT_TOKEN, OWNER_ID]):
    raise ValueError("Missing essential environment variables. Please check your .env file.")

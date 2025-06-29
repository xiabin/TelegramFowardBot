from pyrogram import Client
import uvloop

from config import API_ID, API_HASH, BOT_TOKEN, PROXY

client_params = {
    "name": "TeleFwdBot",
    "api_id": API_ID,
    "api_hash": API_HASH,
    "bot_token": BOT_TOKEN,
    "plugins": {
        "root": "bot.handlers"
    }
}
if PROXY:
    client_params["proxy"] = PROXY


bot_client = Client(**client_params) 
import os
import glob
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters

# --- 1. Purane kharab session files ko auto delete (ye error fix karega) ---
for f in glob.glob("*.session*") + glob.glob("**/*.session*", recursive=True):
    try:
        os.remove(f)
        print(f"Deleted old session file: {f}")
    except:
        pass

# --- 2. ENV se Config ---
API_ID = int(os.environ.get("API_ID", "34125301"))
API_HASH = os.environ.get("API_HASH", "ca9767c009a8e421ef634b101db6d3e3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()

if not SESSION_STRING:
    print("ERROR: SESSION_STRING not found in ENV!")
    exit(1)

print(f"SESSION_STRING length: {len(SESSION_STRING)}")

# Bot Client
bot = Client(
    "film4you_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# User Client - Session String se
user = Client(
    "film4you_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True  # Important: file save nahi karega
)

# --- Tera baki ka code yaha se ---
# Example:
@bot.on_message(filters.command("start"))
async def start(_, m):
    await m.reply_text("Bot Live Hai!")

async def main():
    await bot.start()
    print("Bot Client Started")
    await user.start()
    print("User Client Started - AUTH FIXED!")
    await idle()
    await bot.stop()
    await user.stop()

# Flask for Render health check
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot is Running"

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    from pyrogram import idle
    asyncio.get_event_loop().run_until_complete(main())

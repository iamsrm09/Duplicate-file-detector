import asyncio
# FIX MUST BE AT VERY TOP - BEFORE ANY OTHER IMPORT
try:
    asyncio.set_event_loop(asyncio.new_event_loop())
except Exception:
    pass

import os
from flask import Flask
from threading import Thread

# --- Flask for Render Port Binding ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Film4you Cleaner Live - Bot Running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

Thread(target=run_flask, daemon=True).start()

# --- Telegram Clients (import after loop fix) ---
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Commands ---
@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(client, message):
    await message.reply_text(
        f"Film4you Cleaner Ready\n\nChannel: {CHANNEL_ID}\n\n"
        "/scan - Check duplicates (no delete)\n"
        "/clean - Delete duplicates",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 SCAN NOW", callback_data="scan")],
            [InlineKeyboardButton("🗑️ CLEAN NOW", callback_data="clean")]
        ])
    )

@bot.on_message(filters.command(["scan", "clean"]) & filters.user(OWNER_ID))
async def command_handler(client, message):
    is_clean = "clean" in message.command[0]
    await do_work(client, message, is_clean)

@bot.on_callback_query(filters.user(OWNER_ID))
async def callback_handler(client, query):
    await query.answer("Starting...")
    is_clean = query.data == "clean"
    await do_work(client, query.message, is_clean)

# --- Core Logic ---
async def do_work(client, message, is_clean):
    seen_files = {}
    duplicates = []
    total_scanned = 0
    mode = "CLEAN MODE" if is_clean else "SCAN MODE"

    status = await client.send_message(OWNER_ID, f"{mode}\n\n

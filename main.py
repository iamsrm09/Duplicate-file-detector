import os
import json
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ENV VARIABLES (Render se aayenge) ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

# --- FLASK FOR RENDER ALIVE ---
app_flask = Flask('')
@app_flask.route('/')
def home():
    return f"Film4you Cleaner Live ✅<br>Scanned: {scanned_global} | Deleted: {len(deleted_global)}"
def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
Thread(target=run_flask, daemon=True).start()

# --- PYROGRAM CLIENTS ---
user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

scanned_global = 0
deleted_global = []

# --- BOT COMMANDS ---
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    if m.from_user.id!= OWNER_ID: return
    await m.reply_text(
        f"🎬 **Film4you Professional Cleaner**\n\n"
        f"📁 Channel ID: `{CHANNEL_ID}`\n"
        f"✅ Status: Live & Ready\n\n"
        f"**Commands:**\n"
        f"/scan - Check duplicates (No Delete)\n"
        f"/clean - Auto Delete Duplicates\n"
        f"/report - Last report file\n\n"
        f"Niche button dabaa:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 SCAN NOW", callback_data="scan")],
            [InlineKeyboardButton("🗑️ CLEAN NOW", callback_data="clean")]
        ])
    )

@bot.on_callback_query()
async def cb_handler(c, q):
    if q.from_user.id!= OWNER_ID: return
    await q.answer()
    if q.data == "scan":
        await start_cleaning(c, q.message, delete_mode=False)
    elif q.data == "clean":
        await start_cleaning(c, q.message, delete_mode=True)

@bot.on_message(filters.command(["scan", "clean"]) & filters.private)
async def cmd_handler(c, m):
    if m.from_user.id!= OWNER_ID: return
    delete_mode = "clean" in m.text
    await start_cleaning(c, m, delete_mode)

# --- CORE LOGIC: SCAN + DELETE + REPORT ---
async def start_cleaning(c, message, delete_mode):
    global scanned_global, deleted_global
    scanned_global = 0
    deleted_global = []

    mode_text = "🗑️ **CLEAN MODE** - Delete ON" if delete_mode else "🔍 **SCAN MODE** - Only Checking"
    status = await c.send_message(OWNER_ID, f"{mode_text}\n\n⏳ Starting scan... 0 files")

    seen_uid = {} # file_unique_id -> msg_id
    seen_size = {} # size_duration -> msg_id

    async for msg in user.get_chat_history(CHANNEL_ID):
        file = msg.video or msg.document
        if not file: continue

        scanned_global += 1

        # Update status every 40 files
        if scanned_global % 40 == 0:
            try:
                await status.edit_text(f"{mode_text}\n\n⏳ Scanned: {scanned_global}\n🗑️ Found/Delete: {len(deleted_global)}")
            except: pass

        uid = file.file_unique_id
        size = file.file_size
        size_mb = size / 1024 / 1024
        duration = getattr(file, 'duration', 0)
        name = (msg.caption or file.file_name or "No Name")[:35].replace("\n", " ")

        is_dup = False
        reason = ""

        if uid in seen_uid:
            is_dup = True
            reason = "Same File ID (100% Duplicate)"
        else:
            key = f"{size}_{duration}"
            if key in seen_size and duration!= 0:
                is_dup = True
                reason = f"Same Size+Duration {size_mb:.2f} MB"
            else:
                seen_uid[uid] = msg.id
                seen_size[key] = msg.id

        if is_dup:
            if delete_mode:
                try:
                    await user.delete_messages(CHANNEL_ID, msg.id)
                    deleted_global.append(f"✅ DELETED | {name} | {size_mb:.2f} MB | {reason} | MsgID: {msg.id}")
                except Exception as e:
                    deleted_global.append(f"❌ FAILED | {name} | {size_mb:.2f} MB | Error: {e}")
            else:
                deleted_global.append(f"🔍 FOUND | {name} | {size_mb:.2f} MB | {reason} | MsgID: {msg.id}")

    # --- FINAL PROFESSIONAL REPORT ---
    total_saved = 0
    for line in deleted_global:
        try:
            if "MB" in line:
                mb = float(line.split("|")[2].replace("MB","").strip())
                total_saved += mb
        except: pass

    final_report = f"📊 **PROFESSIONAL CLEAN REPORT**\n\n"
    final_report += f"📁 Channel: {CHANNEL_ID}\n"
    final_report += f"📦 Total Scanned: {scanned_global}\n"
    final_report += f"🗑️ Total {'Deleted' if delete_mode else 'Found'}: {len(deleted_global)}\n"
    final_report += f"💾 Space {'Saved' if delete_mode else 'Wasted'}: {total_saved:.2f} MB ({total_saved/1024:.2f} GB)\n"
    final_report += f"⏰ Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
    final_report += f"**Top 30 List:**\n\n"

    for line in deleted_global[:30]:
        final_report += line + "\n\n"

    if len(deleted_global) > 30:
        final_report += f"\n... and {len(deleted_global)-30} more files. Full list in file."

    if not deleted_global:
        final_report = f"✅ **CLEAN**\n\nTotal Scanned: {scanned_global}\nNo Duplicate Found

import os
import asyncio
import json
from datetime import datetime
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# FIX FOR RENDER PYTHON 3.14
try:
    asyncio.set_event_loop(asyncio.new_event_loop())
except:
    pass

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

# Flask alive
flask_app = Flask('')
@flask_app.route('/')
def home():
    return "Film4you Cleaner Live"
def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
Thread(target=run_flask, daemon=True).start()

user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

scanned_global = 0
deleted_global = []

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    if m.from_user.id!= OWNER_ID:
        return
    await m.reply_text(
        "Film4you Professional Cleaner\n\n"
        f"Channel: {CHANNEL_ID}\nLive & Ready\n\n"
        "/scan - Check duplicates\n"
        "/clean - Delete duplicates\n"
        "/report - Last report",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("SCAN NOW", callback_data="scan")],
            [InlineKeyboardButton("CLEAN NOW", callback_data="clean")]
        ])
    )

@bot.on_callback_query()
async def cb_handler(c, q):
    if q.from_user.id!= OWNER_ID:
        return
    await q.answer()
    if q.data == "scan":
        await start_cleaning(c, q.message, False)
    else:
        await start_cleaning(c, q.message, True)

@bot.on_message(filters.command(["scan", "clean"]) & filters.private)
async def cmd_handler(c, m):
    if m.from_user.id!= OWNER_ID:
        return
    delete_mode = "clean" in m.text
    await start_cleaning(c, m, delete_mode)

async def start_cleaning(c, message, delete_mode):
    global scanned_global, deleted_global
    scanned_global = 0
    deleted_global = []

    mode_text = "CLEAN MODE" if delete_mode else "SCAN MODE"
    status = await c.send_message(OWNER_ID, f"{mode_text}\n\nStarting scan... 0 files")

    seen_uid = {}
    seen_size = {}

    async for msg in user.get_chat_history(CHANNEL_ID):
        file = msg.video or msg.document
        if not file:
            continue

        scanned_global += 1

        if scanned_global % 40 == 0:
            try:
                await status.edit_text(f"{mode_text}\nScanned: {scanned_global}\nFound: {len(deleted_global)}")
            except:
                pass

        uid = file.file_unique_id
        size = file.file_size
        size_mb = size / 1024 / 1024
        duration = getattr(file, 'duration', 0)
        cap = msg.caption or file.file_name or "No Name"
        name = cap[:35].replace("\n", " ")

        is_dup = False
        reason = ""

        if uid in seen_uid:
            is_dup = True
            reason = "Same File ID"
        else:
            key = f"{size}_{duration}"
            if key in seen_size and duration!= 0:
                is_dup = True
                reason = f"Same Size {size_mb:.2f} MB"
            else:
                seen_uid[uid] = msg.id
                seen_size[key] = msg.id

        if is_dup:
            if delete_mode:
                try:
                    await user.delete_messages(CHANNEL_ID, msg.id)
                    deleted_global.append(f"DELETED | {name} | {size_mb:.2f} MB | {reason} | ID:{msg.id}")
                except Exception as e:
                    deleted_global.append(f"FAILED | {name} | {e}")
            else:
                deleted_global.append(f"FOUND | {name} | {size_mb:.2f} MB | {reason} | ID:{msg.id}")

    total_saved = 0
    for line in deleted_global:
        try:
            if "MB" in line:
                mb = float(line.split("|")[2].replace("MB","").strip())
                total_saved += mb
        except:
            pass

    if not deleted_global:
        final_report = f"CLEAN REPORT\n\nScanned: {scanned_global}\nNo Duplicate Found! Channel clean."
    else:
        final_report = f"PROFESSIONAL REPORT\n\n"
        final_report += f"Scanned: {scanned_global}\n"
        if delete_mode:
            final_report += f"Deleted: {len(deleted_global)}\n"
        else:
            final_report += f"Found: {len(deleted_global)}\n"
        final_report += f"Space: {total_saved:.2f} MB ({total_saved/1024:.2f} GB)\n"
        final_report += f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n"
        for line in deleted_global[:30]:
            final_report += line + "\n\n"
        if len(deleted_global) > 30:
            final_report += f"and {len(deleted_global)-30} more..."

    await status.edit_text(final_report)

    if deleted_global:
        with open("Full_Report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(deleted_global))
        await c.send_document(OWNER_ID, "Full_Report.txt", caption=f"Full Report - {len(deleted_global)}")

@bot.on_message(filters.command("report") & filters.private)
async def report_cmd(c, m):
    if m.from_user.id!= OWNER_ID:
        return
    if os.path.exists("Full_Report.txt"):
        await c.send_document(OWNER_ID, "Full_Report.txt")
    else:
        await m.reply_text("No report. Run /scan first.")

async def main():
    await user.start()
    await bot.start()
    print("Film4you Cleaner LIVE - Ready for /scan /clean")
    await idle()
    await user.stop()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

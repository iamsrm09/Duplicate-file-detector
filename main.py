import asyncio
# --- CRITICAL FIX: Must be at top before pyrogram ---
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
except Exception:
    pass

import os
from flask import Flask
from threading import Thread

# Flask for Render Port
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Film4you Cleaner Live - Bot Running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False)

Thread(target=run_flask, daemon=True).start()

# Imports after loop fix
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ENV VARIABLES FROM RENDER ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /start command
@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(c, m):
    await m.reply_text(
        f"🎬 **Film4you Cleaner Ready**\n\n"
        f"Channel: `{CHANNEL_ID}`\n\n"
        f"**Commands:**\n"
        f"/scan - Check duplicates (safe)\n"
        f"/clean - Delete duplicates\n\n"
        f"Bot Live at: https://duplicate-file-detector.onrender.com",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 SCAN NOW", callback_data="scan")],
            [InlineKeyboardButton("🗑️ CLEAN NOW", callback_data="clean")]
        ])
    )

@bot.on_message(filters.command(["scan", "clean"]) & filters.user(OWNER_ID))
async def cmd_handler(c, m):
    is_clean = "clean" in m.command[0]
    await do_work(c, m, is_clean)

@bot.on_callback_query(filters.user(OWNER_ID))
async def cb_handler(c, q):
    await q.answer("Starting task...")
    is_clean = q.data == "clean"
    await do_work(c, q.message, is_clean)

async def do_work(c, message, is_clean):
    seen = {}
    dups = []
    total = 0
    mode = "🗑️ CLEAN MODE" if is_clean else "🔍 SCAN MODE"

    status = await c.send_message(OWNER_ID, f"{mode}\n\nStarting scan... 0 files checked")

    async for msg in user.get_chat_history(CHANNEL_ID):
        f = msg.video or msg.document
        if not f:
            continue

        total += 1
        # Update status every 30 files
        if total % 30 == 0:
            try:
                await status.edit_text(f"{mode}\n\nScanned: {total}\nFound: {len(dups)}")
            except:
                pass

        uid = f.file_unique_id

        if uid in seen:
            if is_clean:
                try:
                    await user.delete_messages(CHANNEL_ID, msg.id)
                    dups.append(f"DELETED | ID:{msg.id} | Original:{seen[uid]}")
                except Exception as e:
                    dups.append(f"FAILED | ID:{msg.id} | Error:{e}")
            else:
                dups.append(f"FOUND | Dup ID:{msg.id} | Original ID:{seen[uid]}")
        else:
            seen[uid] = msg.id

    # Final Report
    if not dups:
        await status.edit_text(f"✅ **No Duplicates Found!**\n\nTotal Files Scanned: {total}")
    else:
        header = f"**{mode} COMPLETE**\n\nScanned: {total}\n{'Deleted' if is_clean else 'Found'}: {len(dups)}\n\n"
        body = "\n".join(dups[:40])
        if len(dups) > 40:
            body += f"\n\n... and {len(dups)-40} more. See Full_Report.txt"

        await status.edit_text(header + body)

        # Send full txt file
        with open("Full_Report.txt", "w", encoding="utf-8") as file:
            file.write("\n".join(dups))
        await c.send_document(OWNER_ID, "Full_Report.txt", caption=f"Full Report - {len(dups)} duplicates")

async def main():
    await user.start()
    await bot.start()
    print("BOT LIVE - READY FOR SCAN / CLEAN")
    await idle()
    await user.stop()
    await bot.stop()

if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(main())

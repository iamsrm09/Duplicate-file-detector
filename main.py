import asyncio
try:
    asyncio.set_event_loop(asyncio.new_event_loop())
except:
    pass

import os
from flask import Flask
from threading import Thread

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Film4you Cleaner Live"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
Thread(target=run_flask, daemon=True).start()

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

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(c, m):
    await m.reply_text(
        "Film4you Cleaner Ready\nChannel: " + str(CHANNEL_ID) + "\n\n/scan - Check\n/clean - Delete",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("SCAN NOW", callback_data="scan")],
            [InlineKeyboardButton("CLEAN NOW", callback_data="clean")]
        ])
    )

@bot.on_message(filters.command(["scan", "clean"]) & filters.user(OWNER_ID))
async def cmd_handler(c, m):
    is_clean = "clean" in m.command[0]
    await do_work(c, m, is_clean)

@bot.on_callback_query(filters.user(OWNER_ID))
async def cb_handler(c, q):
    await q.answer()
    is_clean = q.data == "clean"
    await do_work(c, q.message, is_clean)

async def do_work(c, message, is_clean):
    seen = {}
    dups = []
    total = 0
    mode = "CLEAN MODE" if is_clean else "SCAN MODE"
    status = await c.send_message(OWNER_ID, mode + " Starting... 0 scanned")

    async for msg in user.get_chat_history(CHANNEL_ID):
        f = msg.video or msg.document
        if not f:
            continue
        total += 1
        if total % 30 == 0:
            try:
                await status.edit_text(mode + "\nScanned: " + str(total) + "\nFound: " + str(len(dups)))
            except:
                pass
        uid = f.file_unique_id
        if uid in seen:
            if is_clean:
                try:
                    await user.delete_messages(CHANNEL_ID, msg.id)
                    dups.append("DELETED ID:" + str(msg.id))
                except Exception as e:
                    dups.append("FAILED ID:" + str(msg.id) + " " + str(e))
            else:
                dups.append("FOUND Dup ID:" + str(msg.id) + " Original:" + str(seen[uid]))
        else:
            seen[uid] = msg.id

    if not dups:
        await status.edit_text("No Duplicates! Scanned: " + str(total))
    else:
        text = mode + " DONE\nScanned:" + str(total) + "\nDups:" + str(len(dups)) + "\n\n"
        text += "\n".join(dups[:40])
        await status.edit_text(text)
        with open("Full_Report.txt", "w", encoding="utf-8") as fl:
            fl.write("\n".join(dups))
        await c.send_document(OWNER_ID, "Full_Report.txt")

async def main():
    await user.start()
    await bot.start()
    print("BOT LIVE - READY")
    await idle()
    await user.stop()
    await bot.stop()

if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(main())

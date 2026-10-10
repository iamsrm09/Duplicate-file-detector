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
    return "Active ✅"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

from pyrogram import Client, filters, idle

API_ID = int(os.environ.get("API_ID", "34125301"))
API_HASH = os.environ.get("API_HASH", "ca9767c009a8e421ef634b101db6d3e3")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1004341107282"))
OWNER_ID = int(os.environ.get("OWNER_ID", "7256418269"))

user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(c, m):
    await m.reply_text("Film4you Cleaner Ready\nChannel: " + str(CHANNEL_ID) + "\n\n/scan - Check Duplicates\n/clean - Delete Duplicates")

@bot.on_message(filters.command(["scan", "clean"]) & filters.user(OWNER_ID))
async def cmd_handler(c, m):
    is_clean = "clean" in m.command[0]
    await do_work(c, m, is_clean)

async def do_work(c, message, is_clean):
    seen = {}
    dups = []
    total = 0
    mode = "CLEAN MODE" if is_clean else "SCAN MODE"
    status = await c.send_message(OWNER_ID, mode + " Started... Scanned 0")
    async for msg in user.get_chat_history(CHANNEL_ID):
        f = msg.video or msg.document
        if not f:
            continue
        total += 1
        if total % 30 == 0:
            try:
                await status.edit_text(mode + "\nScanned: " + str(total) + "\nDups: " + str(len(dups)))
            except:
                pass
        uid = f.file_unique_id
        if uid in seen:
            if is_clean:
                try:
                    await user.delete_messages(CHANNEL_ID, msg.id)
                    dups.append("DELETED ID:" + str(msg.id))
                except Exception as e:
                    dups.append("FAILED ID:" + str(msg.id))
            else:
                dups.append("FOUND ID:" + str(msg.id))
        else:
            seen[uid] = msg.id

    if not dups:
        await status.edit_text("No Duplicates! Total Scanned: " + str(total))
    else:
        txt = mode + " DONE\nScanned:" + str(total) + "\nDups:" + str(len(dups)) + "\n\n" + "\n".join(dups[:50])
        await status.edit_text(txt[:4000])

async def main():
    await user.start()
    await bot.start()
    print("BOT LIVE - READY FOR SCAN")
    await idle()
    await user.stop()
    await bot.stop()

if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(main())

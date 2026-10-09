import os, asyncio
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Live - Film4you Cleaner"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), use_reloader=False)
Thread(target=run_flask, daemon=True).start()

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

try:
    asyncio.set_event_loop(asyncio.new_event_loop())
except: pass

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION = os.environ.get("SESSION_STRING")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
OWNER_ID = int(os.environ.get("OWNER_ID"))

user = Client("user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(c, m):
    await m.reply_text(
        f"🎬 Film4you Cleaner Ready\nChannel: {CHANNEL_ID}\n\n/scan - Only Check\n/clean - Delete Duplicates",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 SCAN", callback_data="scan")],
            [InlineKeyboardButton("🗑️ CLEAN", callback_data="clean")]
        ])
    )

@bot.on_message(filters.command(["scan","clean"]) & filters.user(OWNER_ID))
async def scan_clean(c, m):
    is_clean = "clean" in m.command[0]
    await do_work(c, m, is_clean)

@bot.on_callback_query(filters.user(OWNER_ID))
async def cb(c, q):
    is_clean = q.data == "clean"
    await q.answer("Starting...")
    await do_work(c, q.message, is_clean)

async def do_work(c, message, is_clean):
    seen = {}
    dups = []
    total = 0
    mode = "CLEAN" if is_clean else "SCAN"
    sts = await c.send_message(OWNER_ID, f"{mode} Started...\nScanning 0")

    async for msg in user.get_chat_history(CHANNEL_ID):
        f = msg.video or msg.document
        if not f: continue
        total += 1
        if total % 30 == 0:
            try: await sts.edit_text(f"{mode}...\nScanned: {total}\nDups: {len(dups)}")
            except: pass

        uid = f.file_unique_id
        if uid in seen:
            if is_clean:
                try:
                    await user.delete_messages(CHANNEL_ID, msg.id)
                    dups.append(f"DELETED {msg.id}")
                except Exception as e:
                    dups.append(f"FAILED {msg.id} {e}")
            else:
                dups.append(f"FOUND Duplicate MsgID {msg.id} -> Original {seen[uid]}")
        else:
            seen[uid] = msg.id

    if not dups:
        await sts.edit_text(f"✅ No Duplicates!\nTotal Scanned: {total}")
    else:
        txt = f"{mode} DONE\nScanned: {total}\n{'Deleted' if is_clean else 'Found'}: {len(dups)}\n\n" + "\n".join(dups[:40])
        await sts.edit_text(txt)
        with open("report.txt","w") as fl:
            fl.write("\n".join(dups))
        await c.send_document(OWNER_ID, "report.txt")

async def main():
    await user.start()
    await bot.start()
    print("BOT LIVE - READY FOR SCAN")
    await idle()
    await user.stop()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

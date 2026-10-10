import os, glob, asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup

# Cleanup old sessions
for f in glob.glob("*.session*") + glob.glob("**/*.session*", recursive=True):
    try: os.remove(f)
    except: pass

API_ID = int(os.environ.get("API_ID", "34125301"))
API_HASH = os.environ.get("API_HASH", "ca9767c009a8e421ef634b101db6d3e3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "") # e.g. @film4youDataBase - fallback ke liye

if not SESSION_STRING or not BOT_TOKEN:
    print("ENV MISSING"); exit(1)

bot = Client("film4you_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("film4you_user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)

# Buttons
main_keyboard = ReplyKeyboardMarkup(
    [["🔍 Scan", "🗑 Delete Duplicates"], ["📊 Status", "▶️ Start"]],
    resize_keyboard=True
)

# Store duplicates in memory
last_duplicates = []

@bot.on_message(filters.command("start"))
async def start_cmd(_, m):
    await m.reply_text(
        "Bot is Live ✅\n\n🔍 Scan = Check duplicates\n🗑 Delete = Delete duplicates\n📊 Status = Bot status",
        reply_markup=main_keyboard
    )

@bot.on_message(filters.regex("^(▶️ Start|/start)$"))
async def start_btn(_, m):
    await start_cmd(_, m)

@bot.on_message(filters.regex("^(📊 Status|/status)$") | filters.command("status"))
async def status_cmd(_, m):
    await m.reply_text(f"✅ Bot Running\nChannel: {CHANNEL_ID}\nUser Session: Active ({len(SESSION_STRING)} chars)", reply_markup=main_keyboard)

async def get_target_chat():
    # FIX FOR Peer id invalid - pehle dialogs cache karo
    try:
        # 1. Try with ID
        async for dialog in user.get_dialogs():
            if dialog.chat.id == CHANNEL_ID:
                return dialog.chat
    except: pass
    
    try:
        return await user.get_chat(CHANNEL_ID)
    except:
        if CHANNEL_USERNAME:
            return await user.get_chat(CHANNEL_USERNAME)
        raise

@bot.on_message(filters.regex("^(🔍 Scan|/scan)$") | filters.command("scan"))
async def scan_handler(_, m):
    if OWNER_ID != 0 and m.from_user.id != OWNER_ID:
        return
    global last_duplicates
    last_duplicates = []
    
    await m.reply_text(f"Scanning channel {CHANNEL_ID}... Please wait 1-2 min.", reply_markup=main_keyboard)
    try:
        target_chat = await get_target_chat()
        print(f"Channel resolved: {target_chat.id}")

        file_map = {}
        dup_list = []
        total = 0

        async for msg in user.get_chat_history(target_chat.id):
            fid = None
            if msg.document: fid = msg.document.file_unique_id
            elif msg.video: fid = msg.video.file_unique_id
            elif msg.audio: fid = msg.audio.file_unique_id
            
            if not fid: continue
            total += 1
            if fid in file_map:
                dup_list.append(msg)
            else:
                file_map[fid] = msg.id
        
        last_duplicates = dup_list

        if not dup_list:
            await m.reply_text(f"✅ Scan Complete. Checked {total} files. No duplicates found.")
        else:
            await m.reply_text(f"Found {len(dup_list)} duplicate files out of {total}.\n\nPress 🗑 Delete Duplicates to remove them.")

    except Exception as e:
        print(f"SCAN ERROR: {e}")
        await m.reply_text(f"❌ Scan failed: {e}\n\n1. Make sure YOUR account (+91 wala) is joined in the channel\n2. Add CHANNEL_USERNAME in ENV also\n3. Make bot admin in channel")

@bot.on_message(filters.regex("^(🗑 Delete Duplicates|/delete)$") | filters.command("delete"))
async def delete_handler(_, m):
    if OWNER_ID != 0 and m.from_user.id != OWNER_ID: return
    global last_duplicates
    if not last_duplicates:
        await m.reply_text("No duplicates in memory. First press 🔍 Scan.")
        return
    
    await m.reply_text(f"Deleting {len(last_duplicates)} duplicates...")
    deleted = 0
    try:
        target_chat = await get_target_chat()
        for msg in last_duplicates:
            try:
                await user.delete_messages(target_chat.id, msg.id)
                deleted += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Delete fail {msg.id}: {e}")
        
        await m.reply_text(f"✅ Deleted {deleted}/{len(last_duplicates)} duplicate files.")
        last_duplicates = []
    except Exception as e:
        await m.reply_text(f"Delete failed: {e}")

async def main():
    await bot.start()
    print("Bot Started")
    await user.start()
    print("User Started")
    await idle()
    await bot.stop()
    await user.stop()

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot Running"

def run_flask(): app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.get_event_loop().run_until_complete(main())

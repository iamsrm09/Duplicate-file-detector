import os
import glob
import asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle

# --- 1. Auto delete old broken session files ---
for f in glob.glob("*.session*") + glob.glob("**/*.session*", recursive=True):
    try:
        os.remove(f)
        print(f"Deleted old session file: {f}")
    except:
        pass

# --- 2. Load Config from ENV ---
API_ID = int(os.environ.get("API_ID", "34125301"))
API_HASH = os.environ.get("API_HASH", "ca9767c009a8e421ef634b101db6d3e3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))  # e.g., -1003424258306
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

if not SESSION_STRING or not BOT_TOKEN or CHANNEL_ID == 0:
    print("ERROR: SESSION_STRING / BOT_TOKEN / CHANNEL_ID is missing in ENV!")
    exit(1)

print(f"SESSION_STRING length: {len(SESSION_STRING)}")
print(f"Target CHANNEL_ID: {CHANNEL_ID}")

# --- 3. Clients ---
bot = Client("film4you_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("film4you_user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)

@bot.on_message(filters.command("start"))
async def start_cmd(_, m):
    await m.reply_text("Bot is Live! Send /scan to check for duplicates.")

@bot.on_message(filters.command("scan"))
async def scan_handler(_, m):
    if OWNER_ID != 0 and m.from_user.id != OWNER_ID:
        await m.reply_text("You are not authorized to use this command.")
        return

    await m.reply_text(f"Started scanning channel {CHANNEL_ID}... This may take 1-2 minutes.")

    try:
        # Fix for Peer id invalid error - force peer cache
        try:
            await user.get_chat(CHANNEL_ID)
            print("Channel resolved successfully.")
        except Exception as e:
            print(f"get_chat warning: {e}")

        file_map = {}  # file_unique_id -> first message link
        duplicates = []
        total_files = 0

        async for msg in user.get_chat_history(CHANNEL_ID):
            file_unique_id = None
            file_name = None

            if msg.document:
                file_unique_id = msg.document.file_unique_id
                file_name = msg.document.file_name
            elif msg.video:
                file_unique_id = msg.video.file_unique_id
                file_name = msg.video.file_name
            elif msg.audio:
                file_unique_id = msg.audio.file_unique_id
                file_name = msg.audio.file_name

            if not file_unique_id:
                continue

            total_files += 1

            if file_unique_id in file_map:
                duplicates.append(f"Duplicate: {file_name} | First seen: {file_map[file_unique_id]} | Duplicate Msg ID: {msg.id}")
            else:
                file_map[file_unique_id] = msg.id

        if not duplicates:
            await m.reply_text(f"Scan Complete. Checked {total_files} files. No duplicates found.")
        else:
            report = f"Scan Complete. Checked {total_files} files.\nFound {len(duplicates)} duplicates:\n\n" + "\n".join(duplicates[:20])
            if len(duplicates) > 20:
                report += f"\n...and {len(duplicates) - 20} more."
            await m.reply_text(report)

    except Exception as e:
        print(f"Scan Error: {e}")
        await m.reply_text(f"Scan failed: {e}\n\nMake sure your USER account and BOT are both admin in the channel.")

# --- 4. Main Runner ---
async def main():
    await bot.start()
    print("Bot Client Started")
    await user.start()
    print("User Client Started - AUTH FIXED!")
    await idle()
    await bot.stop()
    await user.stop()

# --- 5. Flask for Render ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is Running"

def run_flask():
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.get_event_loop().run_until_complete(main())

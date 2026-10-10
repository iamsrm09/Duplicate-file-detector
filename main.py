import os, glob, asyncio
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Cleanup old sessions
for f in glob.glob("*.session*") + glob.glob("**/*.session*", recursive=True):
    try: os.remove(f)
    except: pass

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")

bot = Client("film4you_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("film4you_user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)

last_duplicates = []

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Scan Duplicates", callback_data="scan")],
        [InlineKeyboardButton("🗑 Delete Duplicates", callback_data="delete"), InlineKeyboardButton("📊 Status", callback_data="status")]
    ])

async def get_target_chat():
    try:
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

@bot.on_message(filters.command("start"))
async def start_cmd(_, m):
    await m.reply_text(
        f"**Film4You Duplicate Manager**\n\n"
        f"**Channel:** `{CHANNEL_ID}`\n"
        f"**Status:** Online ✅\n\n"
        f"Select an action below:",
        reply_markup=main_menu()
    )

@bot.on_callback_query()
async def callback_handler(_, cq):
    data = cq.data
    if data == "scan":
        await cq.message.delete()
        await scan_logic(cq.message)
    elif data == "delete":
        await cq.message.delete()
        await delete_logic(cq.message)
    elif data == "status":
        await cq.answer(f"Bot Online | Duplicates in memory: {len(last_duplicates)}", show_alert=True)

async def scan_logic(message):
    global last_duplicates
    last_duplicates = []

    status_msg = await bot.send_message(message.chat.id, f"**Scanning...**\nChannel: `{CHANNEL_ID}`\nPlease wait, fetching all files.")

    try:
        target_chat = await get_target_chat()
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
            await status_msg.edit_text(
                f"**✅ Scan Complete**\n\n"
                f"**Total Files Checked:** {total}\n"
                f"**Duplicates Found:** 0\n\n"
                f"Your channel is clean. No action needed.",
                reply_markup=main_menu()
            )
        else:
            await status_msg.edit_text(
                f"**⚠️ Scan Complete - Duplicates Found**\n\n"
                f"**Total Files Checked:** {total}\n"
                f"**Duplicates Found:** {len(dup_list)}\n"
                f"**Storage Wasted:** ~{len(dup_list)} files\n\n"
                f"Click Delete to remove them in background. You can close this chat, it will continue.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🗑 Delete {len(dup_list)} Files", callback_data="delete")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="scan")]
                ])
            )

    except Exception as e:
        await status_msg.edit_text(f"**❌ Scan Failed**\n\nError: `{e}`\n\nMake sure your user account is joined in channel and CHANNEL_USERNAME is set in ENV.", reply_markup=main_menu())

async def delete_logic(message):
    global last_duplicates
    if not last_duplicates:
        await bot.send_message(message.chat.id, "**No duplicates in memory.**\nPlease run Scan first.", reply_markup=main_menu())
        return

    total_to_delete = len(last_duplicates)
    progress_msg = await bot.send_message(message.chat.id, f"**🗑 Deletion Started**\n\nProgress: 0/{total_to_delete}")

    deleted = 0
    failed = 0
    try:
        target_chat = await get_target_chat()
        for msg in last_duplicates[:]:
            try:
                await user.delete_messages(target_chat.id, msg.id)
                deleted += 1
            except:
                failed += 1

            if deleted % 10 == 0 or deleted == total_to_delete:
                try:
                    await progress_msg.edit_text(
                        f"**🗑 Deleting in Background...**\n\n"
                        f"**Progress:** {deleted}/{total_to_delete}\n"
                        f"**Deleted:** {deleted}\n"
                        f"**Failed:** {failed}\n\n"
                        f"_You can go back, process will continue._"
                    )
                except: pass
            await asyncio.sleep(0.6)

        last_duplicates = []
        await bot.send_message(message.chat.id, f"**✅ Deletion Finished**\n\n**Total Deleted:** {deleted}\n**Failed:** {failed}", reply_markup=main_menu())

    except Exception as e:
        await bot.send_message(message.chat.id, f"**Delete Error:** `{e}`", reply_markup=main_menu())

@bot.on_message(filters.command(["scan", "delete", "status"]))
async def cmd_handler(_, m):
    if OWNER_ID!= 0 and m.from_user.id!= OWNER_ID: return
    if m.text.startswith("/scan"): await scan_logic(m)
    elif m.text.startswith("/delete"): await delete_logic(m)
    else:
        await m.reply_text(f"**Status: Online**\nDuplicates in memory: {len(last_duplicates)}", reply_markup=main_menu())

async def main():
    await bot.start()
    await user.start()
    print("Both Started")
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

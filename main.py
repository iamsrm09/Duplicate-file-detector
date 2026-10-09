import os
print("Starting bot...")
BOT_TOKEN = os.environ.get('BOT_TOKEN')
print(f"Token found: {BOT_TOKEN is not None}")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN missing!")
    # Don't crash, keep flask alive to see logs
    from flask import Flask
    app = Flask('')
    @app.route('/')
    def home(): return "BOT_TOKEN MISSING - Add in Render Environment"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
else:
    import json, telebot
    from flask import Flask
    from threading import Thread

    FILE_DB = {}
    DB_FILE = "duplicate.json"
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                FILE_DB = json.load(f)
        except:
            FILE_DB = {}
    def save_db():
        with open(DB_FILE, 'w') as f:
            json.dump(FILE_DB, f)

    bot = telebot.TeleBot(BOT_TOKEN)
    app = Flask('')
    @app.route('/')
    def home(): return "Bot Live ✅ No Mongo"
    def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
    Thread(target=run, daemon=True).start()

    @bot.message_handler(commands=['start'])
    def start(m):
        bot.send_message(m.chat.id, "✅ Duplicate Bot Ready!")

    @bot.message_handler(content_types=['video','document','photo'])
    def check(m):
        file = m.video or m.document or (m.photo[-1] if m.photo else None)
        if not file: return
        uid = file.file_unique_id
        size_mb = (file.file_size or 0) / 1024 / 1024
        if uid in FILE_DB:
            bot.reply_to(m, f"❌ DUPLICATE HAI! Size: {size_mb:.2f} MB")
            return
        FILE_DB[uid] = {"file_id": file.file_id, "size": file.file_size or 0, "duration": getattr(file, 'duration', 0), "name": m.caption or ""}
        save_db()
        bot.reply_to(m, f"✅ SAVED! {size_mb:.2f} MB")

    print("Bot polling started...")
    bot.remove_webhook()
    bot.polling(none_stop=True)

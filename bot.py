import logging
import os
import re
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Flask Server for Render (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "YouTube Thumbnail Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
# @BotFather থেকে পাওয়া টোকেনটি এখানে দিন
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ইউটিউব ইউআরএল থেকে ভিডিও আইডি বের করার লজিক (Regex)
def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **YouTube Thumbnail Downloader**-এ স্বাগতম!\n\n"
        "যেকোনো ইউটিউব ভিডিওর লিঙ্ক পাঠান, আমি আপনাকে সেটির HD থাম্বনেইল পাঠিয়ে দেব।"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    video_id = extract_video_id(url)

    if not video_id:
        await update.message.reply_text("❌ এটি সঠিক ইউটিউব লিঙ্ক নয়। দয়া করে সঠিক লিঙ্ক পাঠান।")
        return

    # ইউটিউব থাম্বনেইলের বিভিন্ন কোয়ালিটি ইউআরএল
    # maxresdefault হলো সবথেকে হাই কোয়ালিটি (HD)
    hd_thumbnail = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    sd_thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    try:
        # প্রথমে HD ছবি পাঠানোর চেষ্টা করবে
        await update.message.reply_photo(
            photo=hd_thumbnail,
            caption=f"✅ **HD Thumbnail Downloaded**\n\nLink: {url}",
            parse_mode='Markdown'
        )
    except Exception:
        try:
            # যদি HD না থাকে (পুরাতন ভিডিওর ক্ষেত্রে), তবে স্ট্যান্ডার্ড কোয়ালিটি পাঠাবে
            await update.message.reply_photo(
                photo=sd_thumbnail,
                caption=f"✅ **Standard Quality Thumbnail**\n(HD not available for this video)\n\nLink: {url}",
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text("❌ দুঃখিত, থাম্বনেইলটি পাওয়া যায়নি।")

def main():
    keep_alive() # রেন্ডারে ২৪ ঘণ্টা সচল রাখতে
    app_bot = Application.builder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("YouTube Thumbnail Bot is Online!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

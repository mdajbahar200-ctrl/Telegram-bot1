import logging
import os
from gtts import gTTS
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Flask Server for Render (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "TTS Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
# @BotFather থেকে পাওয়া আপনার টোকেনটি এখানে দিন
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **TTS Bot**-এ স্বাগতম!\n\n"
        "আপনি যা লিখে পাঠাবেন, আমি সেটা আপনাকে ভয়েস মেসেজ হিসেবে শুনিয়ে দেব।\n"
        "বাংলা বা ইংরেজি যেকোনো কিছু লিখে পাঠান!"
    )

async def handle_text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if not user_text:
        return

    # ইউজারকে জানানো হচ্ছে কাজ চলছে
    status_msg = await update.message.reply_text("🎙️ Processing your voice... please wait.")

    try:
        # Google Text-to-Speech ব্যবহার করে অডিও তৈরি (বাংলা অটো ডিটেক্ট করবে)
        tts = gTTS(text=user_text, lang='bn') 
        
        audio_file = "voice.mp3"
        tts.save(audio_file)

        # টেলিগ্রামে ভয়েস মেসেজ হিসেবে পাঠানো
        with open(audio_file, 'rb') as voice:
            await update.message.reply_voice(voice=voice)
        
        # কাজ শেষে অডিও ফাইলটি ডিলিট করে দেওয়া (সার্ভার পরিষ্কার রাখতে)
        os.remove(audio_file)
        await status_msg.delete()

    except Exception as e:
        logging.error(e)
        await status_msg.edit_text("❌ দুঃখিত, ভয়েস তৈরি করতে সমস্যা হয়েছে।")

def main():
    keep_alive() # রেন্ডারে ২৪ ঘণ্টা সচল রাখতে
    app_bot = Application.builder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_to_speech))
    
    print("TTS Bot is Online!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

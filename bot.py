import logging
import os
import asyncio
import edge_tts
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Flask Server ---
app = Flask('')
@app.route('/')
def home(): return "Human Voice Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'

# কন্ঠ সেট করা (বাংলা প্রফেশনাল কন্ঠ)
# অপশন ১: 'bn-BD-NabanitaNeural' (মেয়েদের কন্ঠ)
# অপশন ২: 'bn-BD-PradeepNeural' (ছেলেদের কন্ঠ)
VOICE = 'bn-BD-NabanitaNeural'

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

async def handle_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    status_msg = await update.message.reply_text("🎙️ মানুষের কন্ঠে রূপান্তর করা হচ্ছে...")

    output_file = "human_voice.mp3"
    
    try:
        # Edge TTS দিয়ে অডিও তৈরি
        communicate = edge_tts.Communicate(user_text, VOICE)
        await communicate.save(output_file)

        # ভয়েস মেসেজ পাঠানো
        with open(output_file, 'rb') as voice:
            await update.message.reply_voice(voice=voice)
        
        os.remove(output_file)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ এরর: {str(e)}")

def main():
    keep_alive()
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tts))
    app_bot.run_polling()

if __name__ == '__main__':
    main()

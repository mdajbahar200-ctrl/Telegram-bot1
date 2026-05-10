import logging
import os
import requests
import urllib.parse
import random
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Flask Server for Render (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "AI Image Bot is running 24/7!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}! 👋\n\nI am your **AI Image Generator Bot**.\n"
        "Just send me a message describing the image you want to create.\n\n"
        "Example: `A cat wearing a spacesuit on Mars`"
    )

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    
    if not user_prompt:
        return

    # ইউজারকে জানানো হচ্ছে কাজ শুরু হয়েছে
    status_msg = await update.message.reply_text("🎨 Creating your masterpiece... please wait a moment.")

    try:
        # প্রম্পটকে ইউআরএল ফরম্যাটে কনভার্ট করা
        encoded_prompt = urllib.parse.quote(user_prompt)
        
        # Pollinations AI URL (Flux model for high quality)
        seed = random.randint(1, 999999)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={seed}&model=flux"

        # টেলিগ্রামে সরাসরি ছবি পাঠানো
        await update.message.reply_photo(
            photo=image_url,
            caption=f"✨ **Result for:** {user_prompt}\n\nGenerated with AI 🚀",
            parse_mode='Markdown'
        )
        
        # আগের স্ট্যাটাস মেসেজ ডিলিট করা
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text("❌ Failed to generate image. Please try again with a different description.")

def main():
    # Render এ ২৪ ঘণ্টা সচল রাখতে keep_alive কল করা হয়েছে
    keep_alive()
    
    # বট অ্যাপ্লিকেশন তৈরি
    app_bot = Application.builder().token(TOKEN).build()
    
    # হ্যান্ডলার যুক্ত করা
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))
    
    print("AI Image Generator Bot is Online!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

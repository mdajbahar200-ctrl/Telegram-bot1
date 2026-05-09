import logging
import requests
import random
import string
import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Flask Server for Render (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render assigns a port automatically
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'
API_URL = "https://www.1secmail.com/api/v1/action"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def generate_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📧 Generate New Mail", callback_data='gen_email')],
        [InlineKeyboardButton("📥 Check Inbox", callback_data='check_inbox'),
         InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')],
        [InlineKeyboardButton("🗑️ Delete Session", callback_data='delete_mail')],
        [InlineKeyboardButton("📢 Support", url="https://t.me/Rafi_gaming99")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}! 👋\nI am your personal **Temp Mail Bot**.\nUse the buttons below to manage your emails:",
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Processing...") 

    if query.data == 'gen_email':
        user = generate_username()
        domain = "1secmail.com"
        email = f"{user}@{domain}"
        context.user_data['email'] = email
        context.user_data['user'] = user
        context.user_data['domain'] = domain
        
        # The email is inside backticks, making it "Click-to-Copy"
        text = (
            f"✨ **New Email Generated!**\n\n"
            f"📧 **Email:** `{email}`\n\n"
            f"Tap the email address to copy it. Click **Check Inbox** when you receive a message."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif query.data == 'check_inbox':
        user = context.user_data.get('user')
        domain = context.user_data.get('domain')
        if not user:
            await query.edit_message_text("❌ No active session found! Please generate an email first.", reply_markup=main_menu_keyboard())
            return
        
        response = requests.get(f"{API_URL}?action=getMessages&login={user}&domain={domain}").json()
        if not response:
            await query.edit_message_text(
                f"📭 **Email:** `{context.user_data['email']}`\n\n"
                f"**Inbox is currently empty.** Click Refresh if you are waiting for a code.", 
                parse_mode='Markdown', 
                reply_markup=main_menu_keyboard()
            )
        else:
            msg_list = f"📩 **Inbox for `{context.user_data['email']}`:**\n\n"
            for msg in response[:3]:
                msg_id = msg['id']
                details = requests.get(f"{API_URL}?action=readMessage&login={user}&domain={domain}&id={msg_id}").json()
                msg_list += f"👤 **From:** {msg['from']}\n📌 **Subject:** {msg['subject']}\n📝 **Message:** `{details['textBody']}`\n---\n"
            
            # Message bodies also set to click-to-copy for easy OTP extraction
            await query.edit_message_text(msg_list, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif query.data == 'delete_mail':
        context.user_data.clear()
        await query.edit_message_text("🗑️ Session deleted successfully. Click below to start over.", reply_markup=main_menu_keyboard())

def main():
    keep_alive() # Starts Flask Server
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    print("Bot and Keep-Alive Server Started!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

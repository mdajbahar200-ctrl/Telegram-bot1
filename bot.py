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
    # Render assigns a port automatically via environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
# Re-check your token if you revoked it.
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
        
        text = (
            f"✨ **New Email Generated!**\n\n"
            f"📧 **Email:** `{email}`\n\n"
            f"Tap the email above to copy. Click **Check Inbox** when you expect a message."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif query.data == 'check_inbox':
        user = context.user_data.get('user')
        domain = context.user_data.get('domain')
        
        if not user:
            await query.edit_message_text("❌ No active session found! Generate a new email first.", reply_markup=main_menu_keyboard())
            return
        
        try:
            # Added error handling for the JSON decoding issue
            response = requests.get(f"{API_URL}?action=getMessages&login={user}&domain={domain}")
            
            if response.status_code != 200:
                await query.edit_message_text("⚠️ API Server is busy. Please try refreshing again in a few seconds.", reply_markup=main_menu_keyboard())
                return
            
            data = response.json()
            
            if not data:
                await query.edit_message_text(
                    f"📭 **Email:** `{context.user_data['email']}`\n\n"
                    f"**Inbox is empty.** Wait a few moments and click Refresh.", 
                    parse_mode='Markdown', 
                    reply_markup=main_menu_keyboard()
                )
            else:
                msg_list = f"📩 **Inbox for `{context.user_data['email']}`:**\n\n"
                for msg in data[:3]:
                    msg_id = msg['id']
                    # Fetching individual message body
                    msg_details = requests.get(f"{API_URL}?action=readMessage&login={user}&domain={domain}&id={msg_id}").json()
                    msg_list += f"👤 **From:** {msg['from']}\n📌 **Subject:** {msg['subject']}\n📝 **Message:** `{msg_details['textBody']}`\n---\n"
                
                await query.edit_message_text(msg_list, parse_mode='Markdown', reply_markup=main_menu_keyboard())
        
        except Exception as e:
            logging.error(f"Error: {e}")
            await query.edit_message_text("❌ Error connecting to the mail server. Please try again later.", reply_markup=main_menu_keyboard())

    elif query.data == 'delete_mail':
        context.user_data.clear()
        await query.edit_message_text("🗑️ Session deleted. Ready to generate a new email.", reply_markup=main_menu_keyboard())

def main():
    keep_alive() # Essential for Render
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is alive and running on Render!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

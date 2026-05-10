import logging
import requests
import random
import string
import os
import time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Flask Server for Render ---
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'
MAIL_TM_API = "https://api.mail.tm"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📧 Generate Mail (Premium)", callback_data='gen_mail')],
        [InlineKeyboardButton("📥 Check Inbox", callback_data='check_inbox')],
        [InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')],
        [InlineKeyboardButton("🗑️ Clear Session", callback_data='delete_mail')],
        [InlineKeyboardButton("📢 Support", url="https://t.me/Rafi_gaming99")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Pro Temp Mail Bot (2026 Edition)**\n\nI am now using **Mail.tm & Internxt** technology to ensure you get OTPs instantly.\n\nClick below to get your email:",
        reply_markup=main_menu(), parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'gen_mail':
        try:
            # Step 1: Get available domain from Mail.tm
            domain_res = requests.get(f"{MAIL_TM_API}/domains").json()
            domain = domain_res['hydra:member'][0]['domain']
            
            # Step 2: Create Account
            username = f"{generate_random_string()}@{domain}"
            password = generate_random_string()
            
            acc_res = requests.post(f"{MAIL_TM_API}/accounts", json={
                "address": username,
                "password": password
            })
            
            if acc_res.status_code == 201:
                # Step 3: Get Token
                token_res = requests.post(f"{MAIL_TM_API}/token", json={
                    "address": username,
                    "password": password
                }).json()
                
                context.user_data.update({
                    'email': username,
                    'token': token_res['token'],
                    'id': acc_res.json()['id']
                })
                
                await query.edit_message_text(
                    f"✨ **New Premium Email:**\n`{username}`\n\n✅ This email works on Facebook, Google, and more.\n✅ Tap to copy. Then click **Check Inbox**.",
                    parse_mode='Markdown', reply_markup=main_menu()
                )
            else:
                await query.edit_message_text("❌ Failed to generate mail. Try again.", reply_markup=main_menu())
        except Exception as e:
            logging.error(e)
            await query.edit_message_text("⚠️ Service currently busy. Please try again in a moment.", reply_markup=main_menu())

    elif query.data == 'check_inbox':
        token = context.user_data.get('token')
        email = context.user_data.get('email')
        
        if not token:
            await query.edit_message_text("❌ No active session! Generate a mail first.", reply_markup=main_menu())
            return

        headers = {"Authorization": f"Bearer {token}"}
        try:
            # Fetch messages
            res = requests.get(f"{MAIL_TM_API}/messages", headers=headers).json()
            messages = res.get('hydra:member', [])
            
            if not messages:
                await query.edit_message_text(
                    f"📭 **Email:** `{email}`\n\n**Status:** No messages yet. (Send your OTP and wait 30 seconds)", 
                    parse_mode='Markdown', reply_markup=main_menu()
                )
            else:
                msg_text = f"📩 **Inbox for `{email}`:**\n\n"
                for m in messages[:3]:
                    # Fetch full message body
                    m_id = m['id']
                    m_data = requests.get(f"{MAIL_TM_API}/messages/{m_id}", headers=headers).json()
                    msg_text += f"👤 **From:** {m['from']['name'] or m['from']['address']}\n📌 **Subject:** {m['subject']}\n📝 **Message:** `{m_data['intro'] or 'Tap to view content'}`\n---\n"
                
                await query.edit_message_text(msg_text, parse_mode='Markdown', reply_markup=main_menu())
        except Exception:
            await query.edit_message_text("❌ Connection error. Try Refresh.", reply_markup=main_menu())

    elif query.data == 'delete_mail':
        context.user_data.clear()
        await query.edit_message_text("🗑️ Session deleted. Generate a new one.", reply_markup=main_menu())

def main():
    keep_alive()
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running with Mail.tm API!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Settings ---
TOKEN = '8691093894:AAE_BONWwZbanaHBTlJJqAFx3cPY2f_s5rk'
API_URL = "https://www.1secmail.com/api/v1/action"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Top 5 Best Domains (No Login Required) ---
DOMAINS = [
    "1secmail.com", 
    "1secmail.org", 
    "1secmail.net",
    "kzbox.me",      # High success rate
    "vjuum.com"      # Alternative domain
]

def generate_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📧 Generate New Mail", callback_data='gen_email')],
        [InlineKeyboardButton("📥 Check Inbox", callback_data='check_inbox'),
         InlineKeyboardButton("🔄 Refresh", callback_data='check_inbox')],
        [InlineKeyboardButton("🌐 Switch Domain (5 Options)", callback_data='switch_domain')],
        [InlineKeyboardButton("🗑️ Delete Session", callback_data='delete_mail')],
        [InlineKeyboardButton("📢 Support", url="https://t.me/Rafi_gaming99")]
    ]
    return InlineKeyboardMarkup(keyboard)

def domain_selection_keyboard():
    keyboard = []
    # Creating a grid of domains
    for domain in DOMAINS:
        keyboard.append([InlineKeyboardButton(f"🔹 {domain}", callback_data=f"set_dom_{domain}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_main')])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hi {user_name}! 👋\nWelcome to your **Advanced Temp Mail Bot**.\nI provide 5 different domains for better OTP success!",
        reply_markup=main_menu_keyboard(),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Working...") 

    if query.data == 'gen_email':
        user = generate_username()
        # Default to first domain if not selected
        domain = context.user_data.get('domain', DOMAINS[0])
        email = f"{user}@{domain}"
        
        context.user_data['email'] = email
        context.user_data['user'] = user
        context.user_data['domain'] = domain
        
        text = (
            f"✅ **Temp Mail Ready!**\n\n"
            f"📧 **Address:** `{email}`\n"
            f"🌐 **Domain:** {domain}\n\n"
            f"Tap the email to copy. If you don't get the OTP, try another domain from 'Switch Domain'."
        )
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    elif query.data == 'switch_domain':
        await query.edit_message_text("⚙️ **Select your preferred domain:**\n\nTips: If one domain is blocked by a site, try another one from this list.", 
                                      reply_markup=domain_selection_keyboard(), parse_mode='Markdown')

    elif query.data.startswith('set_dom_'):
        new_domain = query.data.replace('set_dom_', '')
        context.user_data['domain'] = new_domain
        await query.edit_message_text(f"✅ **Selected:** {new_domain}\nNow click 'Generate' to get an email with this domain.", 
                                      reply_markup=main_menu_keyboard(), parse_mode='Markdown')

    elif query.data == 'check_inbox':
        user = context.user_data.get('user')
        domain = context.user_data.get('domain')
        
        if not user:
            await query.edit_message_text("❌ No active email! Click Generate first.", reply_markup=main_menu_keyboard())
            return
        
        try:
            response = requests.get(f"{API_URL}?action=getMessages&login={user}&domain={domain}")
            if response.status_code != 200:
                await query.edit_message_text("⚠️ Server lag. Please refresh in 5 seconds.", reply_markup=main_menu_keyboard())
                return
            
            data = response.json()
            if not data:
                await query.edit_message_text(f"📭 **Mail:** `{context.user_data['email']}`\n\n**Status:** Inbox is empty. Waiting for message...", 
                                              parse_mode='Markdown', reply_markup=main_menu_keyboard())
            else:
                msg_list = f"📩 **Inbox for `{context.user_data['email']}`:**\n\n"
                for msg in data[:3]:
                    msg_id = msg['id']
                    msg_details = requests.get(f"{API_URL}?action=readMessage&login={user}&domain={domain}&id={msg_id}").json()
                    msg_list += f"👤 **From:** {msg['from']}\n📌 **Sub:** {msg['subject']}\n📝 **OTP/Body:** `{msg_details['textBody']}`\n---\n"
                await query.edit_message_text(msg_list, parse_mode='Markdown', reply_markup=main_menu_keyboard())
        except:
            await query.edit_message_text("❌ Connection error. Try again.", reply_markup=main_menu_keyboard())

    elif query.data == 'back_to_main':
        await query.edit_message_text("How can I help you today?", reply_markup=main_menu_keyboard())

    elif query.data == 'delete_mail':
        context.user_data.clear()
        await query.edit_message_text("🗑️ Session cleared successfully.", reply_markup=main_menu_keyboard())

def main():
    keep_alive() # For Render 24/7
    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running with 5 Domains!")
    app_bot.run_polling()

if __name__ == '__main__':
    main()

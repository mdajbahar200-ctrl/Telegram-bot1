import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, 
    MessageHandler, filters, ConversationHandler, ContextTypes
)

# আপনার টেলিগ্রাম আইডি এখানে দিন (অ্যাডমিন প্যানেল এক্সেস করার জন্য)
ADMIN_ID = "6878641639" 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# স্টেটসমূহ
TYPING_NAME, TYPING_PRICE, TYPING_PHOTO = range(3)

def init_db():
    conn = sqlite3.connect('market.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price TEXT, photo_id TEXT, seller_id TEXT, status TEXT DEFAULT 'active')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, role TEXT DEFAULT 'user')''')
    conn.commit()
    conn.close()

init_db()

# --- ১. ইউজার প্যানেল (Buyers) ---
def user_menu():
    keyboard = [
        [InlineKeyboardButton("🛍 প্রোডাক্ট ব্রাউজ করুন", callback_data='buy_all')],
        [InlineKeyboardButton("📜 আমার অর্ডার", callback_data='my_orders')],
        [InlineKeyboardButton("🧑‍💻 সেলার প্যানেলে যান", callback_data='seller_home')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- ২. সেলার প্যানেল (Sellers) ---
def seller_menu():
    keyboard = [
        [InlineKeyboardButton("➕ নতুন প্রোডাক্ট অ্যাড", callback_data='list_item')],
        [InlineKeyboardButton("📦 আমার লিস্টিং", callback_data='my_listings')],
        [InlineKeyboardButton("💰 মোট বিক্রয়", callback_data='stats')],
        [InlineKeyboardButton("🔙 মেইন মেনু", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- ৩. অ্যাডমিন প্যানেল (Admin Only) ---
def admin_menu():
    keyboard = [
        [InlineKeyboardButton("📊 বোট স্ট্যাটস", callback_data='admin_stats')],
        [InlineKeyboardButton("🚫 ইউজার ব্যান করুন", callback_data='ban_user')],
        [InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data='broadcast')],
        [InlineKeyboardButton("🔙 মেইন মেনু", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # অ্যাডমিন চেক
    if user_id == ADMIN_ID:
        text = "👑 স্বাগতম বস! এটি আপনার অ্যাডমিন প্যানেল।"
        reply_markup = admin_menu()
    else:
        text = "👋 স্বাগতম! আমাদের মার্কেটপ্লেসে আপনার কি প্রয়োজন?"
        reply_markup = user_menu()

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

# প্যানেল সুইচিং হ্যান্ডলার
async def handle_panels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'seller_home':
        await query.edit_text("👨‍💼 সেলার ড্যাশবোর্ড\nএখান থেকে আপনার ইনভেন্টরি ম্যানেজ করুন।", reply_markup=seller_menu())
    elif query.data == 'main_menu':
        await start(update, context)

# --- আগের লিস্টিং ফাংশনগুলো এখানে থাকবে ---
# (কোড ছোট করার জন্য সব ফাংশন পুনরায় লেখা হলো না, তবে আগের কোডের মতো get_name, get_photo কাজ করবে)

def main():
    TOKEN = "8831236489:AAHKvJWV2PQCZwzQ3Sg3Yx1klXK08Jut4gE"
    app = Application.builder().token(TOKEN).build()

    # হ্যান্ডলার অ্যাড
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_panels, pattern='^(seller_home|main_menu)$'))
    
    # অন্যান্য লজিক (buy_all, list_item ইত্যাদি) যুক্ত করুন...

    print("মার্কেটপ্লেস বোট ৩টি প্যানেলসহ চালু হচ্ছে...")
    app.run_polling()

if __name__ == '__main__':
    main()

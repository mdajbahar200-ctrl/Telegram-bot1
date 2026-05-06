import asyncio
import logging
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Render-এর জন্য Flask সার্ভার ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- কনফিগারেশন ---
API_TOKEN = '8629069708:AAFrAwq3U4FU1yOlEITgbhTzKrJDhOCSosM'
ADMIN_ID = 123456789  # <--- এখানে আপনার টেলিগ্রাম আইডি বসান

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- কিবোর্ডসমূহ ---

def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🛒 Buy Products", callback_data="buy_list")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="my_profile"),
         InlineKeyboardButton(text="💳 Deposit", callback_data="add_money")],
        [InlineKeyboardButton(text="📞 Support", url="https://t.me/Rafi_gaming99")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_menu():
    buttons = [
        [InlineKeyboardButton(text="➕ Add Product", callback_data="admin_add")],
        [InlineKeyboardButton(text="💰 Change Balance", callback_data="admin_bal")],
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_bc")],
        [InlineKeyboardButton(text="🔙 Exit Admin", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def product_list_menu():
    products = [
        {"name": "420495xx:USD$2111", "price": 2500, "id": "p1"},
        {"name": "435880xx:USD$500", "price": 600, "id": "p2"},
        {"name": "461126xx:CAD$500", "price": 550, "id": "p3"},
    ]
    keyboard = []
    for p in products:
        keyboard.append([
            InlineKeyboardButton(text=f"✅ {p['name']}", callback_data="info"),
            InlineKeyboardButton(text="🛒 Purchase", callback_data=f"buy_{p['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton(text="💳 Visa", callback_data="v"),
        InlineKeyboardButton(text="🟠 Master", callback_data="m"),
        InlineKeyboardButton(text="🔵 Amex", callback_data="a")
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu"),
        InlineKeyboardButton(text="🔄 Refresh", callback_data="buy_list")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- ইউজার হ্যান্ডলারসমূহ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"⚜️ **CentsCard Gift Cards Exchange Bot** ⚜️\n\n"
        f"👤 **Welcome** {message.from_user.first_name} 🥳\n"
        f"💰 **Account Balance:** $0.24\n"
        f"📢 **STOCK Updates:** [Notify Channel](https://t.me/Rafi_gaming99)\n"
    )
    await message.answer(welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "buy_list")
async def process_buy_list(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text="🛍 **Available Listings:**\nFalse = Not used on PayPal\nTrue = Used on PayPal",
        reply_markup=product_list_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "main_menu")
async def process_back_main(callback: types.CallbackQuery):
    welcome_text = (
        f"⚜️ **CentsCard Gift Cards Exchange Bot** ⚜️\n\n"
        f"💰 **Account Balance:** $0.24"
    )
    try:
        await callback.message.edit_text(welcome_text, reply_markup=main_menu(), parse_mode="Markdown")
    except:
        await callback.message.answer(welcome_text, reply_markup=main_menu(), parse_mode="Markdown")
    await callback.answer()

# --- এডমিন হ্যান্ডলারসমূহ ---

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 **Admin Panel**\nবট নিয়ন্ত্রণের অপশন সিলেক্ট করুন:", reply_markup=admin_menu(), parse_mode="Markdown")
    else:
        await message.answer("❌ আপনি এই বটের এডমিন নন!")

@dp.callback_query(F.data.startswith("admin_"))
async def process_admin_actions(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("অ্যাক্সেস ডিনাইড!", show_alert=True)
    
    if callback.data == "admin_add":
        await callback.message.answer("📝 নতুন প্রোডাক্ট যোগ করার সিস্টেম ডেভেলপ করা হচ্ছে...")
    elif callback.data == "admin_bal":
        await callback.message.answer("💰 ব্যালেন্স পরিবর্তনের অপশন শীঘ্রই আসছে...")
    elif callback.data == "admin_bc":
        await callback.message.answer("📢 ব্রডকাস্ট মেসেজ টাইপ করুন (সিস্টেম আপডেটিং...)")
    await callback.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: types.CallbackQuery):
    await callback.answer(text="❌ পর্যাপ্ত ব্যালেন্স নেই! $0.24 আছে।", show_alert=True)

# --- মেইন ফাংশন ---

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")

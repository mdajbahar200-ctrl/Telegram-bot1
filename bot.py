import asyncio
import logging
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

# --- Render-এর জন্য Flask সার্ভার ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    # Render সাধারণত 10000 পোর্টে রান করে
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -----------------------------------

API_TOKEN = '8629069708:AAFrAwq3U4FU1yOlEITgbhTzKrJDhOCSosM'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🛒 Buy Products", callback_data="buy_list")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="my_profile"),
         InlineKeyboardButton(text="💳 Deposit", callback_data="add_money")],
        [InlineKeyboardButton(text="📞 Support", url="t.me/Rafi_gaming99")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def product_list_menu():
    products = [
        {"name": "Visa Gift Card ($5)", "price": 450, "id": "v5"},
        {"name": "Mastercard ($10)", "price": 900, "id": "m10"},
        {"name": "Netflix Premium", "price": 300, "id": "nf"},
    ]
    buttons = [[InlineKeyboardButton(text=f"{p['name']} - {p['price']} BDT", callback_data=f"buy_{p['id']}")] for p in products]
    buttons.append([InlineKeyboardButton(text="🔙 Back to Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"👋 স্বাগতম **{message.from_user.first_name}**!\n\n💰 ব্যালেন্স: **০.০০ টাকা**", reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "buy_list")
async def process_buy_list(callback: types.CallbackQuery):
    await callback.message.edit_text(text="🛍 **প্রোডাক্ট লিস্ট:**", reply_markup=product_list_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def process_back_main(callback: types.CallbackQuery):
    await callback.message.edit_text(text=f"💰 ব্যালেন্স: **০.০০ টাকা**", reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: types.CallbackQuery):
    await callback.answer(text="❌ পর্যাপ্ত ব্যালেন্স নেই!", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive() # Flask সার্ভার চালু করবে
    asyncio.run(main())

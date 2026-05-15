import asyncio
import aiosqlite
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================

TOKEN = "8831236489:AAEkQ5en6RNZkyzuSSxkSrVimtg2BkdJAAg"
ADMIN_ID = 6878641639

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================

async def init_db():
    async with aiosqlite.connect("market.db") as db:
        # প্রডাক্ট টেবিল
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            title TEXT,
            price TEXT,
            description TEXT
        )
        """)
        # ইউজার ব্যালেন্স টেবিল
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
        """)
        await db.commit()

# ইউজার যদি নতুন হয় তবে ডাটাবেসে অ্যাড করা
async def check_user(user_id):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                await db.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
                await db.commit()

# ================= MAIN MENU =================

def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Products", callback_data="products")],
            [InlineKeyboardButton(text="➕ Add Product", callback_data="add_product")],
            [InlineKeyboardButton(text="👤 Profile", callback_data="profile")]
        ]
    )

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await check_user(message.from_user.id)
    await message.answer(
        f"🔥 Welcome To Marketplace Bot, {message.from_user.first_name}!",
        reply_markup=get_main_menu()
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    await check_user(call.from_user.id)
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (call.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

    text = (
        f"👤 User ID: {call.from_user.id}\n"
        f"📛 Name: {call.from_user.full_name}\n"
        f"💰 Balance: {balance} BDT"
    )
    await call.message.edit_text(text, reply_markup=get_main_menu())

# ================= ADMIN PANEL & BALANCE CONTROL =================

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT COUNT(*) FROM products") as cursor:
            total_products = await cursor.fetchone()
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = await cursor.fetchone()

    text = (
        f"⚙️ **Admin Panel**\n\n"
        f"📦 Total Products: {total_products[0]}\n"
        f"👥 Total Users: {total_users[0]}\n\n"
        f"**ব্যালেন্স আপডেট করার নিয়ম:**\n"
        f"`/setbalance [USER_ID] [AMOUNT]`\n"
        f"উদাহরণ: `/setbalance 12345678 500`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("setbalance"))
async def set_balance(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        args = message.text.split()
        target_user_id = int(args[1])
        new_balance = float(args[2])

        async with aiosqlite.connect("market.db") as db:
            await db.execute("INSERT OR REPLACE INTO users (user_id, balance) VALUES (?, ?)", (target_user_id, new_balance))
            await db.commit()

        await message.answer(f"✅ User `{target_user_id}` এর নতুন ব্যালেন্স: `{new_balance}` BDT")
        
        # ইউজারকে নোটিফিকেশন পাঠানো
        try:
            await bot.send_message(target_user_id, f"💰 এডমিন আপনার ব্যালেন্স আপডেট করেছেন।\nবর্তমান ব্যালেন্স: {new_balance} BDT")
        except:
            pass

    except (IndexError, ValueError):
        await message.answer("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/setbalance USER_ID AMOUNT`")

# ================= (বাকি কোডগুলো আগের মতোই থাকবে) =================
# [add_product, product_steps, products, buy_product ফাংশনগুলো এখানে বসবে]

async def main():
    await init_db()
    # Conflict এড়াতে drop_pending_updates=True ব্যবহার করা ভালো
    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")

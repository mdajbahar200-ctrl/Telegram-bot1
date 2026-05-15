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
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# ================= CONFIG =================
TOKEN = "8831236489:AAEkQ5en6RNZkyzuSSxkSrVimtg2BkdJAAg"
ADMIN_ID = 6878641639

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STATES (FSM) =================
class AddProduct(StatesGroup):
    title = State()
    price = State()
    description = State()

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect("market.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            title TEXT,
            price REAL,
            description TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
        """)
        await db.commit()

async def check_user(user_id):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                await db.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
                await db.commit()

# ================= KEYBOARDS =================
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="🛒 Products", callback_data="view_products")],
        [InlineKeyboardButton(text="➕ Add Product", callback_data="add_product_start")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_btn():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]])

# ================= START & PROFILE =================
@dp.message(CommandStart())
async def start(message: Message):
    await check_user(message.from_user.id)
    await message.answer(f"🔥 Welcome To Marketplace Bot, {message.from_user.first_name}!", reply_markup=get_main_menu())

@dp.callback_query(F.data == "back_to_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("🔥 Welcome To Marketplace Bot!", reply_markup=get_main_menu())

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (call.from_user.id,)) as cursor:
            row = await cursor.fetchone()
            balance = row[0] if row else 0.0

    text = f"👤 User ID: `{call.from_user.id}`\n📛 Name: {call.from_user.full_name}\n💰 Balance: {balance} BDT"
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_btn())

# ================= VIEW & BUY PRODUCTS =================
@dp.callback_query(F.data == "view_products")
async def view_products(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT id, title, price FROM products") as cursor:
            products = await cursor.fetchall()

    if not products:
        return await call.message.edit_text("❌ বর্তমানে কোনো প্রডাক্ট নেই।", reply_markup=get_back_btn())

    keyboard = []
    for p_id, title, price in products:
        keyboard.append([InlineKeyboardButton(text=f"{title} - {price} BDT", callback_data=f"info_{p_id}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])
    
    await call.message.edit_text("🛍️ আমাদের প্রডাক্ট লিস্ট:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@dp.callback_query(F.data.startswith("info_"))
async def product_info(call: CallbackQuery):
    p_id = int(call.data.split("_")[1])
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT title, price, description FROM products WHERE id = ?", (p_id,)) as cursor:
            product = await cursor.fetchone()

    if product:
        title, price, desc = product
        text = f"📦 **{title}**\n\n📝 বর্ণনা: {desc}\n💰 দাম: {price} BDT"
        kb = [
            [InlineKeyboardButton(text="💳 Buy Now", callback_data=f"buy_{p_id}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="view_products")]
        ]
        await call.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(call: CallbackQuery):
    p_id = int(call.data.split("_")[1])
    user_id = call.from_user.id

    async with aiosqlite.connect("market.db") as db:
        # প্রডাক্টের দাম চেক
        async with db.execute("SELECT title, price FROM products WHERE id = ?", (p_id,)) as cursor:
            product = await cursor.fetchone()
        
        # ইউজারের ব্যালেন্স চেক
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_data = await cursor.fetchone()
            balance = user_data[0] if user_data else 0

        if product and balance >= product[1]:
            new_balance = balance - product[1]
            await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            await db.commit()
            await call.message.answer(f"✅ কেনা সফল হয়েছে!\n📦 প্রডাক্ট: {product[0]}\n💰 খরচ: {product[1]} BDT\n📉 বর্তমান ব্যালেন্স: {new_balance} BDT")
            await call.answer("Success!")
        else:
            await call.answer("❌ পর্যাপ্ত ব্যালেন্স নেই!", show_alert=True)

# ================= ADD PRODUCT (FSM) =================
@dp.callback_query(F.data == "add_product_start")
async def add_product_start(call: CallbackQuery, state: FSMContext):
    await call.message.answer("📝 প্রডাক্টের নাম দিন:")
    await state.set_state(AddProduct.title)
    await call.answer()

@dp.message(AddProduct.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("💰 প্রডাক্টের দাম দিন (শুধু সংখ্যা):")
    await state.set_state(AddProduct.price)

@dp.message(AddProduct.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer("📄 প্রডাক্টের বিস্তারিত বর্ণনা দিন:")
        await state.set_state(AddProduct.description)
    except ValueError:
        await message.answer("❌ ভুল! দাম শুধু সংখ্যায় লিখুন (যেমন: 500)।")

@dp.message(AddProduct.description)
async def process_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect("market.db") as db:
        await db.execute("INSERT INTO products (seller_id, title, price, description) VALUES (?, ?, ?, ?)",
                         (message.from_user.id, data['title'], data['price'], message.text))
        await db.commit()
    
    await message.answer("✅ প্রডাক্ট সফলভাবে অ্যাড হয়েছে!", reply_markup=get_main_menu())
    await state.clear()

# ================= ADMIN PANEL =================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT COUNT(*) FROM products") as c1, db.execute("SELECT COUNT(*) FROM users") as c2:
            tp, tu = await c1.fetchone(), await c2.fetchone()

    text = f"⚙️ **Admin Panel**\n📦 Products: {tp[0]}\n👥 Users: {tu[0]}\n\nব্যালেন্স সেট করতে লিখুন:\n`/setbalance USER_ID AMOUNT`"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("setbalance"))
async def set_balance(message: Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        uid, amt = args[1], args[2]
        async with aiosqlite.connect("market.db") as db:
            await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (float(amt), int(uid)))
            await db.commit()
        await message.answer(f"✅ User `{uid}` এর ব্যালেন্স `{amt}` BDT করা হয়েছে।")
    except:
        await message.answer("❌ ফরম্যাট ভুল! উদাহরণ: `/setbalance 12345 500`")

# ================= RUNNER =================
async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

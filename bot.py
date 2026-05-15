import asyncio
import logging
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

# ================= CONFIG =================

# Updated with your provided token
TOKEN = "8831236489:AAFjpi1sDF880JF-hoiWTRfASITql0cdGcw"

ADMIN_ID = 6361822194  # Replace this with your actual Telegram User ID

bot = Bot(
    token=TOKEN,
    parse_mode=ParseMode.HTML
)

dp = Dispatcher(
    storage=MemoryStorage()
)

logging.basicConfig(level=logging.INFO)

# ================= STATES =================

class AddProduct(StatesGroup):
    title = State()
    price = State()
    category = State()
    description = State()
    photo = State()

# ================= DATABASE =================

async def init_db():
    async with aiosqlite.connect("market.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            title TEXT,
            price REAL,
            category TEXT,
            description TEXT,
            photo TEXT,
            status TEXT DEFAULT 'pending'
        )
        """)
        await db.commit()

# ================= USER CHECK =================

async def check_user(user_id):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute(
            "SELECT user_id FROM users WHERE user_id=?",
            (user_id,)
        ) as cursor:
            user = await cursor.fetchone()

        if not user:
            await db.execute(
                "INSERT INTO users (user_id, balance) VALUES (?, ?)",
                (user_id, 0)
            )
            await db.commit()

# ================= KEYBOARDS =================

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Browse Products", callback_data="products")],
            [InlineKeyboardButton(text="➕ Sell Product", callback_data="add_product")],
            [InlineKeyboardButton(text="📦 My Products", callback_data="my_products")],
            [InlineKeyboardButton(text="👤 Profile", callback_data="profile")]
        ]
    )

def back_btn():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
        ]
    )

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await check_user(message.from_user.id)
    await message.answer(
        "🔥 Welcome to the Marketplace Bot",
        reply_markup=main_menu()
    )

# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.message.edit_text(
        "🏠 Main Menu",
        reply_markup=main_menu()
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (call.from_user.id,)
        ) as cursor:
            row = await cursor.fetchone()

    balance = row[0] if row else 0
    text = (
        f"<b>👤 Profile</b>\n\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"📛 Name: {call.from_user.full_name}\n"
        f"💰 Balance: {balance} BDT"
    )
    await call.message.edit_text(text, reply_markup=back_btn())

# ================= ADD PRODUCT =================

@dp.callback_query(F.data == "add_product")
async def add_product(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.title)
    await call.message.answer("📦 Enter Product Title:")

@dp.message(AddProduct.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("💰 Enter Product Price:")

@dp.message(AddProduct.price)
async def add_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer("❌ Invalid format. Please enter a number:")
    
    await state.update_data(price=price)
    await state.set_state(AddProduct.category)
    await message.answer("📂 Enter Category:")

@dp.message(AddProduct.category)
async def add_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("📝 Enter Description:")

@dp.message(AddProduct.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.photo)
    await message.answer("🖼 Upload Product Photo:")

@dp.message(AddProduct.photo)
async def add_photo(message: Message, state: FSMContext):
    if not message.photo:
        return await message.answer("❌ Please upload a photo.")

    photo = message.photo[-1].file_id
    data = await state.get_data()

    async with aiosqlite.connect("market.db") as db:
        await db.execute(
            """
            INSERT INTO products
            (seller_id, title, price, category, description, photo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.from_user.id,
                data['title'],
                data['price'],
                data['category'],
                data['description'],
                photo
            )
        )
        await db.commit()

    await state.clear()
    await message.answer("✅ Product Successfully Submitted", reply_markup=main_menu())

# ================= PRODUCTS =================

@dp.callback_query(F.data == "products")
async def products(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT id, title, price FROM products") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await call.message.edit_text("❌ No Products Found", reply_markup=back_btn())

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(text=f"{row[1]} - {row[2]} BDT", callback_data=f"view_{row[0]}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back")])

    await call.message.edit_text(
        "🛒 Available Products",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# ================= VIEW PRODUCT =================

@dp.callback_query(F.data.startswith("view_"))
async def view_product(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    async with aiosqlite.connect("market.db") as db:
        async with db.execute(
            "SELECT seller_id, title, price, category, description, photo FROM products WHERE id=?",
            (product_id,)
        ) as cursor:
            product = await cursor.fetchone()

    if not product:
        return

    seller_id, title, price, category, desc, photo = product
    text = (
        f"<b>📦 {title}</b>\n\n"
        f"📂 Category: {category}\n"
        f"💰 Price: {price} BDT\n\n"
        f"📝 {desc}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Buy Now", callback_data=f"buy_{product_id}")],
            [InlineKeyboardButton(text="📩 Contact Seller", url=f"tg://user?id={seller_id}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="products")]
        ]
    )
    await call.message.answer_photo(photo, caption=text, reply_markup=keyboard)

# ================= BUY PRODUCT =================

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(call: CallbackQuery):
    await call.answer("✅ Order Sent Successfully")

# ================= MY PRODUCTS =================

@dp.callback_query(F.data == "my_products")
async def my_products(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute(
            "SELECT id, title FROM products WHERE seller_id=?",
            (call.from_user.id,)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await call.message.edit_text("❌ You have no products for sale.", reply_markup=back_btn())

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(text=f"🗑 Delete {row[1]}", callback_data=f"delete_{row[0]}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back")])

    await call.message.edit_text(
        "📦 Your Product Listings",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# ================= DELETE PRODUCT =================

@dp.callback_query(F.data.startswith("delete_"))
async def delete_product(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    async with aiosqlite.connect("market.db") as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()
    await call.answer("✅ Product Deleted")

# ================= SEARCH =================

@dp.message(Command("search"))
async def search(message: Message):
    text = message.text.replace("/search", "").strip()
    if not text:
        return await message.answer("❌ Example: /search netflix")

    async with aiosqlite.connect("market.db") as db:
        async with db.execute(
            "SELECT id, title, price FROM products WHERE title LIKE ?",
            (f"%{text}%",)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.answer("❌ No matches found.")

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(text=f"{row[1]} - {row[2]} BDT", callback_data=f"view_{row[0]}")
        ])
    
    await message.answer("🔎 Search Results:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# ================= ADMIN =================

@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ Admin Panel Access Granted")

# ================= CANCEL =================

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Action cancelled.", reply_markup=main_menu())

# ================= RUN =================

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")

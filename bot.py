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
from aiogram.filters import CommandStart
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
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            title TEXT,
            price TEXT,
            description TEXT
        )
        """)
        await db.commit()

# ================= MAIN MENU =================

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Products", callback_data="products")],
        [InlineKeyboardButton(text="➕ Add Product", callback_data="add_product")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")]
    ]
)

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"🔥 Welcome To Marketplace Bot, {message.from_user.first_name}!",
        reply_markup=main_menu
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    text = (
        f"👤 User ID: {call.from_user.id}\n"
        f"📛 Name: {call.from_user.full_name}"
    )
    await call.message.edit_text(text, reply_markup=main_menu)

# ================= ADD PRODUCT =================

user_step = {}
product_data = {}

@dp.callback_query(F.data == "add_product")
async def add_product(call: CallbackQuery):
    user_step[call.from_user.id] = "title"
    await call.message.answer("📦 Product Title পাঠাও")
    await call.answer()

@dp.message(F.text & ~F.text.startswith("/"))
async def product_steps(message: Message):
    user_id = message.from_user.id
    if user_id not in user_step:
        return

    step = user_step[user_id]

    if step == "title":
        product_data[user_id] = {"title": message.text}
        user_step[user_id] = "price"
        await message.answer("💰 Product Price পাঠাও")

    elif step == "price":
        product_data[user_id]["price"] = message.text
        user_step[user_id] = "description"
        await message.answer("📝 Product Description পাঠাও")

    elif step == "description":
        product_data[user_id]["description"] = message.text
        data = product_data[user_id]

        async with aiosqlite.connect("market.db") as db:
            await db.execute(
                "INSERT INTO products (seller_id, title, price, description) VALUES (?, ?, ?, ?)",
                (user_id, data["title"], data["price"], data["description"])
            )
            await db.commit()

        del user_step[user_id]
        del product_data[user_id]
        await message.answer("✅ Product Added Successfully", reply_markup=main_menu)

# ================= PRODUCTS =================

@dp.callback_query(F.data == "products")
async def products(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT * FROM products") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await call.message.answer("❌ No Products Found")
        await call.answer()
        return

    for row in rows:
        p_id, s_id, title, price, desc = row
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛍 Buy Now", callback_data=f"buy_{p_id}")],
                [InlineKeyboardButton(text="📩 Contact Seller", url=f"tg://user?id={s_id}")]
            ]
        )
        text = f"📦 {title}\n💰 Price: {price}\n📝 {desc}"
        await call.message.answer(text, reply_markup=keyboard)
    await call.answer()

# ================= BUY =================

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(call: CallbackQuery):
    product_id = call.data.split("_")[1]
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT seller_id, title FROM products WHERE id=?", (product_id,)) as cursor:
            product = await cursor.fetchone()

    if product:
        seller_id, title = product
        try:
            await bot.send_message(seller_id, f"🛒 New Order Received For: {title}\nBuyer ID: {call.from_user.id}")
            await call.message.answer("✅ Order Sent To Seller")
        except:
            await call.message.answer("❌ Seller cannot be notified.")
    await call.answer()

# ================= ADMIN PANEL =================

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT COUNT(*) FROM products") as cursor:
            total_products = await cursor.fetchone()

    await message.answer(f"⚙️ Admin Panel\n\n📦 Total Products: {total_products[0]}")

# ================= RUN =================

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")

import asyncio
import logging
import aiosqlite
import os # পোর্ট রিড করার জন্য যোগ করা হয়েছে

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
from aiohttp import web # ওয়েব সার্ভার সচল করার জন্য লাইব্রেরি যুক্ত করা হয়েছে

# ================= CONFIG =================

TOKEN = "8831236489:AAHhsnleyAXVfVt0M9PI1oee2t18bwxvveE"
ADMIN_ID = 6878641639

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
                (user_id, 500)
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
        "🔥 Welcome To Marketplace Bot",
        reply_markup=main_menu()
    )

# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_text(
            "🏠 Main Menu",
            reply_markup=main_menu()
        )
    except Exception:
        await call.message.delete()
        await call.message.answer(
            "🏠 Main Menu",
            reply_markup=main_menu()
        )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    await check_user(call.from_user.id)
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

    await call.message.edit_text(
        text,
        reply_markup=back_btn()
    )

# ================= ADD PRODUCT =================

@dp.callback_query(F.data == "add_product")
async def add_product(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.title)
    await call.message.edit_text("📦 Please send the Product Title:")

@dp.message(AddProduct.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("💰 Please send the Product Price (Numbers only):")

@dp.message(AddProduct.price)
async def add_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer("❌ Invalid input! Please enter numbers only (e.g., 500):")

    await state.update_data(price=price)
    await state.set_state(AddProduct.category)
    await message.answer("📂 Please send the Category name:")

@dp.message(AddProduct.category)
async def add_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("📝 Please send the Product Description:")

@dp.message(AddProduct.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.photo)
    await message.answer("🖼 Please upload a Product Photo:")

@dp.message(AddProduct.photo)
async def add_photo(message: Message, state: FSMContext):
    if not message.photo:
        return await message.answer("❌ Invalid input! Please send an actual image file:")

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
    await message.answer(
        "✅ Product Successfully Submitted!",
        reply_markup=main_menu()
    )

# ================= PRODUCTS =================

@dp.callback_query(F.data == "products")
async def products(call: CallbackQuery):
    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT id, title, price FROM products") as cursor:
            rows = await cursor.fetchall()

    if not rows:
        try:
            return await call.message.edit_text("❌ No Products Found", reply_markup=back_btn())
        except Exception:
            await call.message.delete()
            return await call.message.answer("❌ No Products Found", reply_markup=back_btn())

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(text=f"{row[1]} - {row[2]}৳", callback_data=f"view_{row[0]}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back")])

    try:
        await call.message.edit_text("🛒 Product List", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except Exception:
        await call.message.delete()
        await call.message.answer("🛒 Product List", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

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
        return await call.answer("❌ Product not found!", show_alert=True)

    seller_id, title, price, category, desc, photo = product

    text = (
        f"<b>📦 {title}</b>\n\n"
        f"📂 Category: {category}\n"
        f"💰 Price: {price} BDT\n"
        f"👤 Seller ID: {seller_id}\n\n"
        f"📝 Description:\n{desc}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Buy Now", callback_data=f"buy_{product_id}")],
            [InlineKeyboardButton(text="📩 Contact Seller", url=f"tg://user?id={seller_id}")],
            [InlineKeyboardButton(text="🔙 Back to List", callback_data="products")]
        ]
    )

    await call.message.delete()
    await call.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=keyboard
    )

# ================= BUY PRODUCT =================

@dp.callback_query(F.data.startswith("buy_"))
async def buy_product(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    buyer_id = call.from_user.id

    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT seller_id, title, price FROM products WHERE id=?", (product_id,)) as cursor:
            product = await cursor.fetchone()
        
        if not product:
            return await call.answer("❌ Product not found!", show_alert=True)
        
        seller_id, title, price = product

        if buyer_id == seller_id:
            return await call.answer("❌ You cannot buy your own product!", show_alert=True)

        async with db.execute("SELECT balance FROM users WHERE user_id=?", (buyer_id,)) as cursor:
            buyer_row = await cursor.fetchone()
        
        buyer_balance = buyer_row[0] if buyer_row else 0

        if buyer_balance < price:
            return await call.answer(f"❌ Insufficient balance! Required: {price} BDT", show_alert=True)

        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, buyer_id))
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, seller_id))
        await db.commit()

    await call.answer("✅ Order placed successfully!", show_alert=True)

    try:
        await bot.send_message(
            chat_id=seller_id,
            text=f"🎉 <b>Your product has been sold!</b>\n\n📦 Item: {title}\n💰 Price: {price} BDT\n👤 Buyer: <a href='tg://user?id={buyer_id}'>{call.from_user.full_name}</a>"
        )
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📢 <b>New Successful Order!</b>\n\n📦 Item: {title}\n💰 Price: {price} BDT\n👤 Buyer ID: {buyer_id}\n👤 Seller ID: {seller_id}"
        )
    except Exception as e:
        logging.error(f"Notification error: {e}")

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
        try:
            return await call.message.edit_text("❌ You Have No Products", reply_markup=back_btn())
        except Exception:
            await call.message.delete()
            return await call.message.answer("❌ You Have No Products", reply_markup=back_btn())

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(text=f"🗑 Delete: {row[1]}", callback_data=f"delete_{row[0]}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back")])

    try:
        await call.message.edit_text("📦 Your Products (Click to delete):", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except Exception:
        await call.message.delete()
        await call.message.answer("📦 Your Products (Click to delete):", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# ================= DELETE PRODUCT =================

@dp.callback_query(F.data.startswith("delete_"))
async def delete_product(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])

    async with aiosqlite.connect("market.db") as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()

    await call.answer("✅ Product Deleted Successfully!")
    await my_products(call)

# ================= SEARCH =================

@dp.message(Command("search"))
async def search(message: Message):
    text = message.text.replace("/search", "").strip()

    if not text:
        return await message.answer("❌ Usage format:\n<code>/search netflix</code>")

    async with aiosqlite.connect("market.db") as db:
        async with db.execute(
            "SELECT id, title, price FROM products WHERE title LIKE ?",
            (f"%{text}%",)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.answer("❌ No matching products found!")

    keyboard = []
    for row in rows:
        keyboard.append([
            InlineKeyboardButton(text=f"{row[1]} - {row[2]}৳", callback_data=f"view_{row[0]}")
        ])

    await message.answer(
        "🔎 Search Results:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# ================= ADMIN =================

@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("market.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM products") as c2:
            total_products = (await c2.fetchone())[0]

    await message.answer(
        f"⚙️ <b>Admin Panel</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📦 Total Products: {total_products}"
    )

# ================= CANCEL =================

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Action cancelled.",
        reply_markup=main_menu()
    )

# ================= WEB SERVER FOR RENDER =================

async def web_handle(request):
    return web.Response(text="Bot is running successfully on Render Web Service!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', web_handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render পরিবেশ থেকে অটোমেটিক পোর্ট রিসিভ করবে, লোকালি টেস্ট করার জন্য ডিফোল্ট ৮০৮০
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Render Web Server started on port {port}")

# ================= RUN =================

async def main():
    await init_db()
    
    # বটের মেইন ইভেন্ট লুপের সাথে ওয়েব সার্ভারটি প্যারালালি ব্যাকগ্রাউন্ডে রান করানো হচ্ছে
    await start_web_server() 

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

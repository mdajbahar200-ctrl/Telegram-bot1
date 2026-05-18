import asyncio
import logging
import random
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
from aiogram.enums import ParseMode

# ================= CONFIG =================

# আপনার দেওয়া বট টোকেন এবং অ্যাডমিন আইডি এখানে বসানো হয়েছে
TOKEN = "8831236489:AAFEVdxOyZcHfgA77nTT0D8Bt6roNsYZXXg"

ADMIN_ID = 6878641639

BOT_USERNAME = "YourBotUsername" # আপনার বটের ইউজারনেম এখানে দিতে পারেন (@ ছাড়া)

bot = Bot(
    token=TOKEN,
    parse_mode=ParseMode.HTML
)

dp = Dispatcher(
    storage=MemoryStorage()
)

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================

async def init_db():

    async with aiosqlite.connect("earning.db") as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            level TEXT DEFAULT 'Bronze'
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            reward REAL,
            link TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS completed_tasks (
            user_id INTEGER,
            task_id INTEGER
        )
        """)

        await db.commit()

# ================= USER CHECK =================

async def check_user(user_id):

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT user_id FROM users WHERE user_id=?",
            (user_id,)
        ) as cursor:

            user = await cursor.fetchone()

        if not user:

            await db.execute(
                "INSERT INTO users (user_id) VALUES (?)",
                (user_id,)
            )

            await db.commit()

# ================= MENU =================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 Tasks",
                    callback_data="tasks"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Wallet",
                    callback_data="wallet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Referral",
                    callback_data="referral"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Daily Bonus",
                    callback_data="bonus"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Profile",
                    callback_data="profile"
                )
            ]
        ]
    )

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):

    await check_user(message.from_user.id)

    await message.answer(
        "🔥 Welcome To Earning Bot\n\n"
        "🎯 Complete Tasks\n"
        "💰 Earn Money\n"
        "👥 Invite Friends",
        reply_markup=main_menu()
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT balance, referrals, level FROM users WHERE user_id=?",
            (call.from_user.id,)
        ) as cursor:

            user = await cursor.fetchone()

    balance, referrals, level = user

    text = (
        f"<b>👤 Profile</b>\n\n"
        f"🆔 ID: <code>{call.from_user.id}</code>\n"
        f"💰 Balance: {balance} BDT\n"
        f"👥 Referrals: {referrals}\n"
        f"🏆 Level: {level}"
    )

    await call.message.edit_text(
        text,
        reply_markup=main_menu()
    )

# ================= TASKS =================

@dp.callback_query(F.data == "tasks")
async def tasks(call: CallbackQuery):

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT id, title, reward FROM tasks"
        ) as cursor:

            rows = await cursor.fetchall()

    if not rows:

        return await call.message.edit_text(
            "❌ No Tasks Available",
            reply_markup=main_menu()
        )

    keyboard = []

    for row in rows:

        keyboard.append([
            InlineKeyboardButton(
                text=f"{row[1]} - {row[2]}৳",
                callback_data=f"task_{row[0]}"
            )
        ])

    await call.message.edit_text(
        "🎯 Available Tasks",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

# ================= TASK VIEW =================

@dp.callback_query(F.data.startswith("task_"))
async def task_view(call: CallbackQuery):

    task_id = int(call.data.split("_")[1])

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT title, reward, link FROM tasks WHERE id=?",
            (task_id,)
        ) as cursor:

            task = await cursor.fetchone()

    if not task:
        return

    title, reward, link = task

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Start Task",
                    url=link
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Complete Task",
                    callback_data=f"complete_{task_id}"
                )
            ]
        ]
    )

    text = (
        f"🎯 {title}\n\n"
        f"💰 Reward: {reward} BDT"
    )

    await call.message.edit_text(
        text,
        reply_markup=keyboard
    )

# ================= COMPLETE TASK =================

@dp.callback_query(F.data.startswith("complete_"))
async def complete_task(call: CallbackQuery):

    task_id = int(call.data.split("_")[1])

    user_id = call.from_user.id

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT * FROM completed_tasks WHERE user_id=? AND task_id=?",
            (user_id, task_id)
        ) as cursor:

            done = await cursor.fetchone()

        if done:

            return await call.answer(
                "❌ Already Completed",
                show_alert=True
            )

        async with db.execute(
            "SELECT reward FROM tasks WHERE id=?",
            (task_id,)
        ) as cursor:

            task = await cursor.fetchone()

        reward = task[0]

        async with db.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (user_id,)
        ) as cursor:

            user = await cursor.fetchone()

        balance = user[0]

        new_balance = balance + reward

        await db.execute(
            "UPDATE users SET balance=? WHERE user_id=?",
            (new_balance, user_id)
        )

        await db.execute(
            "INSERT INTO completed_tasks (user_id, task_id) VALUES (?, ?)",
            (user_id, task_id)
        )

        await db.commit()

    await call.message.answer(
        f"✅ Task Completed\n\n💰 Earned: {reward} BDT"
    )

# ================= WALLET =================

@dp.callback_query(F.data == "wallet")
async def wallet(call: CallbackQuery):

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (call.from_user.id,)
        ) as cursor:

            user = await cursor.fetchone()

    balance = user[0]

    text = (
        f"💰 Your Wallet\n\n"
        f"Balance: {balance} BDT\n\n"
        f"Minimum Withdraw: 100 BDT"
    )

    await call.message.edit_text(
        text,
        reply_markup=main_menu()
    )

# ================= BONUS =================

@dp.callback_query(F.data == "bonus")
async def bonus(call: CallbackQuery):

    reward = random.randint(1, 10)

    async with aiosqlite.connect("earning.db") as db:

        async with db.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (call.from_user.id,)
        ) as cursor:

            user = await cursor.fetchone()

        balance = user[0]

        new_balance = balance + reward

        await db.execute(
            "UPDATE users SET balance=? WHERE user_id=?",
            (new_balance, call.from_user.id)
        )

        await db.commit()

    await call.answer(
        f"🎁 You Got {reward} BDT Bonus",
        show_alert=True
    )

# ================= REFERRAL =================

@dp.callback_query(F.data == "referral")
async def referral(call: CallbackQuery):

    link = f"https://t.me/{BOT_USERNAME}?start={call.from_user.id}"

    text = (
        f"👥 Invite Friends\n\n"
        f"🎁 Per Referral: 5 BDT\n\n"
        f"🔗 Your Link:\n{link}"
    )

    await call.message.edit_text(
        text,
        reply_markup=main_menu()
    )

# ================= ADMIN =================

@dp.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = (
        "⚙️ Admin Commands\n\n"
        "/addtask Title | Reward | Link\n"
        "/setbalance USER_ID AMOUNT"
    )

    await message.answer(text)

# ================= ADD TASK =================

@dp.message(Command("addtask"))
async def add_task(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        data = message.text.replace("/addtask ", "")

        title, reward, link = data.split("|")

        async with aiosqlite.connect("earning.db") as db:

            await db.execute(
                "INSERT INTO tasks (title, reward, link) VALUES (?, ?, ?)",
                (title.strip(), float(reward), link.strip())
            )

            await db.commit()

        await message.answer("✅ Task Added")

    except:

        await message.answer(
            "❌ Example:\n/addtask YouTube Subscribe | 5 | https://youtube.com"
        )

# ================= SET BALANCE =================

@dp.message(Command("setbalance"))
async def set_balance(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        args = message.text.split()

        user_id = int(args[1])

        amount = float(args[2])

        async with aiosqlite.connect("earning.db") as db:

            await db.execute(
                "UPDATE users SET balance=? WHERE user_id=?",
                (amount, user_id)
            )

            await db.commit()

        await message.answer("✅ Balance Updated")

    except:

        await message.answer(
            "❌ Example:\n/setbalance 123456789 100"
        )

# ================= RUN =================

async def main():

    await init_db()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())

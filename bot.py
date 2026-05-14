import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# লগিং
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# স্টেট
TYPING_NAME, TYPING_PRICE, TYPING_PHOTO = range(3)

# মেনু বাটন ফাংশন
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛍 Buy Product", callback_data='buy'),
         InlineKeyboardButton("➕ List Product", callback_data='list')],
        [InlineKeyboardButton("👤 My Profile", callback_data='profile'),
         InlineKeyboardButton("🆘 Support", callback_data='support')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "স্বাগতম! আপনি কি করতে চান? নিচের বাটন থেকে সিলেক্ট করুন:"
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        await update.callback_query.message.edit_text(text, reply_markup=main_menu_keyboard())

# লিস্টিং শুরু
async def start_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_text("আপনার প্রোডাক্টের নাম লিখুন:")
    return TYPING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_name'] = update.message.text
    await update.message.reply_text(f"'{update.message.text}' এর দাম কত? (শুধু সংখ্যা)")
    return TYPING_PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_price'] = update.message.text
    await update.message.reply_text("প্রোডাক্টের একটি ছবি পাঠান:")
    return TYPING_PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p_name = context.user_data['p_name']
    p_price = context.user_data['p_price']
    
    await update.message.reply_text(
        f"✅ সফলভাবে লিস্ট হয়েছে!\n\n📦 নাম: {p_name}\n💰 দাম: {p_price} টাকা",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বাতিল করা হয়েছে।", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

def main():
    TOKEN = "8831236489:AAHKvJWV2PQCZwzQ3Sg3Yx1klXK08Jut4gE"
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_listing, pattern='^list$')],
        states={
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            TYPING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            TYPING_PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    # সাপোর্ট ও অন্যান্য বাটনের জন্য সিম্পল হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()

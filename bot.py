import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# متغیرهای محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN')  # توکن ربات از متغیر محیطی
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # آی‌دی مدیر از متغیر محیطی

# مراحل احراز هویت
PHONE, PHOTO, VERIFY = range(3)

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("ارسال شماره تلفن", callback_data="send_phone")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"سلام {user.first_name}!\n\n"
        "جهت ورود به گروه مهندسی کامپیوتر مراحل احراز را انجام دهید:",
        reply_markup=reply_markup
    )

# دریافت شماره تلفن
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    phone_number = user.phone_number
    if phone_number:
        context.user_data['phone_number'] = phone_number
        await query.edit_message_text(
            "شماره تلفن شما دریافت شد. لطفاً اکنون اسکرین شات پروفایل آموزشیار خود را ارسال کنید."
        )
        return PHOTO
    else:
        await query.edit_message_text(
            "شماره تلفن شما ثبت نشده است. لطفاً ابتدا شماره تلفن خود را در تنظیمات تلگرام وارد کنید و دوباره تلاش کنید."
        )
        return ConversationHandler.END

# دریافت عکس
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    context.user_data['photo_file'] = photo_file

    await update.message.reply_text(
        "عکس شما دریافت شد. لطفاً منتظر بمانید تا مدیر درخواست شما را بررسی کند."
    )

    # ارسال اطلاعات به مدیر
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo_file,
        caption=f"کاربر {update.effective_user.first_name} با شماره {context.user_data['phone_number']} درخواست عضویت داده است."
    )
    return VERIFY

# تأیید یا رد درخواست توسط مدیر
async def verify_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    if user_input == "تایید":
        user_chat_id = context.user_data.get('user_chat_id')
        await context.bot.send_message(chat_id=user_chat_id, text="درخواست شما تأیید شد. لینک گروه: https://t.me/YOUR_GROUP_LINK")
        return ConversationHandler.END
    elif user_input == "رد":
        user_chat_id = context.user_data.get('user_chat_id')
        await context.bot.send_message(chat_id=user_chat_id, text="درخواست شما رد شد. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً فقط 'تایید' یا 'رد' ارسال کنید.")
        return VERIFY

# لغو فرآیند
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرآیند لغو شد.")
    return ConversationHandler.END

# تنظیمات اصلی ربات
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # تعریف مکالمه چند مرحله‌ای
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()

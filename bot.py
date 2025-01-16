import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
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
        [KeyboardButton("ارسال شماره تلفن", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"سلام {user.first_name}!\n\n"
        "جهت ورود به گروه مهندسی کامپیوتر مراحل احراز را انجام دهید:",
        reply_markup=reply_markup
    )
    return PHONE

# دریافت شماره تلفن
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data['phone_number'] = phone_number
        await update.message.reply_text(
            "شماره تلفن شما دریافت شد. لطفاً اکنون اسکرین شات پروفایل آموزشیار خود را ارسال کنید (راهنما: ثبت نام دروس دانشجو > مشاهده وضعیت)."
        )
        return PHOTO
    else:
        await update.message.reply_text(
            "شماره تلفن شما ارسال نشد. لطفاً دوباره تلاش کنید."
        )
        return PHONE

# دریافت عکس
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
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
    else:
        await update.message.reply_text("لطفاً یک عکس معتبر ارسال کنید.")
        return PHOTO

# تأیید یا رد درخواست توسط مدیر
async def verify_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    user_chat_id = context.user_data.get('user_chat_id')

    if user_input == "تایید":
        await context.bot.send_message(chat_id=user_chat_id, text="درخواست شما تأیید شد. لینک گروه: https://t.me/YOUR_GROUP_LINK")
        return ConversationHandler.END
    elif user_input == "رد":
        await context.bot.send_message(chat_id=user_chat_id, text="درخواست شما رد شد. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً فقط 'تایید' یا 'رد' ارسال کنید.")
        return VERIFY

# نمایش پیام در صورت ارسال پیام غیر مرتبط
async def pending_request_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("درخواست شما در حال بررسی می‌باشد.")

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
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # هندلر برای پیام‌های غیر مرتبط
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, pending_request_message))

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()

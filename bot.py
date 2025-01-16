import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# متغیرهای محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN')  # توکن ربات
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # آی‌دی عددی مدیر

# مراحل
PHONE, PHOTO = range(2)

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[KeyboardButton("ارسال شماره تلفن", request_contact=True)]]
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
        await update.message.reply_text("شماره تلفن ارسال نشد. لطفاً دوباره تلاش کنید.")
        return PHONE

# دریافت عکس
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file = update.message.photo[-1].file_id

        # ذخیره اطلاعات کاربر
        context.user_data['photo_file'] = photo_file

        # ارسال پیام به مدیر
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_file,
            caption=(
                f"درخواست عضویت جدید:\n"
                f"نام: {update.effective_user.first_name}\n"
                f"شماره تلفن: {context.user_data['phone_number']}"
            )
        )
        await update.message.reply_text("عکس شما دریافت شد و درخواست شما در حال بررسی است.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً یک عکس معتبر ارسال کنید.")
        return PHOTO

# لغو فرآیند
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرآیند لغو شد.")
    return ConversationHandler.END

# تنظیمات اصلی
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()

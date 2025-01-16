import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# توکن ربات و لینک گروه
BOT_TOKEN = os.environ.get('BOT_TOKEN')  # توکن ربات از متغیر محیطی خوانده می‌شود
GROUP_LINK = "https://t.me/YOUR_GROUP_LINK"

# مراحل احراز هویت
PHONE, PHOTO, VERIFY = range(3)

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}، جهت ورود به گروه مهندسی کامپیوتر لطفا مراحل احراز را انجام دهید :"
    )
    return PHONE

# دریافت شماره تلفن
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    # بررسی صحت شماره تلفن (مثلاً با الگوی خاص)
    if phone_number.startswith("+98") and len(phone_number) == 13:
        context.user_data['phone_number'] = phone_number
        await update.message.reply_text(
            "شماره تلفن شما دریافت شد. لطفاً اکنون اسکرین شات از پروفایل آموزشیار خودتون بفرستید، از مسیر ثبت نام دروس دانشجو > مشاهده وضعیت :"
        )
        return PHOTO
    else:
        await update.message.reply_text("شماره تلفن معتبر نیست. لطفاً دوباره امتحان کنید.")
        return PHONE

# دریافت عکس
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    context.user_data['photo_file'] = photo_file

    await update.message.reply_text(
        "عکس شما دریافت شد. لطفاً منتظر بمانید تا مدیر آن را بررسی کند."
    )

    # ارسال عکس به مدیر برای تأیید
    admin_chat_id = os.environ.get('ADMIN_CHAT_ID')  # آی‌دی چت مدیر از متغیر محیطی
    await context.bot.send_photo(chat_id=admin_chat_id, photo=photo_file,
                                 caption=f"کاربر {update.effective_user.first_name} با شماره {context.user_data['phone_number']} درخواست عضویت داده است.")
    return VERIFY

# تأیید یا رد درخواست توسط مدیر
async def verify_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    if user_input == "تایید":
        # ارسال لینک گروه به کاربر
        user_chat_id = update.message.reply_to_message.forward_from.id
        await context.bot.send_message(chat_id=user_chat_id, text=f"هویت شما تأیید شد! لینک گروه: {GROUP_LINK}")
        return ConversationHandler.END
    elif user_input == "رد":
        user_chat_id = update.message.reply_to_message.forward_from.id
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

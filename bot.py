import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# متغیرهای محیطی
BOT_TOKEN = os.getenv('BOT_TOKEN')  # توکن ربات از متغیر محیطی
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # آی‌دی مدیر از متغیر محیطی

# مراحل احراز هویت
PHONE, PHOTO, PENDING = range(3)

# حذف وب‌هوک
async def remove_webhook():
    bot = Bot(BOT_TOKEN)
    await bot.delete_webhook()

# دیکشنری ذخیره اطلاعات کاربران
user_requests = {}

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[KeyboardButton("ارسال شماره تلفن", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "جهت ورود به گروه مهندسی کامپیوتر لطفا مراحل احراز را انجام دهید:",
        reply_markup=reply_markup
    )
    user_requests[user_id] = {"status": "waiting_for_phone"}
    return PHONE

# دریافت شماره تلفن
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        user_requests[user_id]["phone_number"] = phone_number
        user_requests[user_id]["status"] = "waiting_for_photo"
        await update.message.reply_text(
            "در ادامه لطفا اسکرین شات از پروفایل آموزشیار خودتون بفرستید، از مسیر ثبت نام دروس دانشجو > مشاهده وضعیت:"
        )
        return PHOTO
    else:
        await update.message.reply_text(
            "شماره تلفن ارسال نشد. لطفاً دوباره تلاش کنید."
        )
        return PHONE

# دریافت عکس
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.photo:
        photo_file = update.message.photo[-1].file_id
        user_requests[user_id]["photo_file"] = photo_file
        user_requests[user_id]["status"] = "pending"

        await update.message.reply_text(
            "عکس شما دریافت شد. درخواست شما به مدیر ارسال شد."
        )

        # ارسال اطلاعات به مدیر
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_file,
            caption=f"کاربر {update.effective_user.first_name} با شماره {user_requests[user_id]['phone_number']} درخواست عضویت داده است."
        )

        return PENDING
    else:
        await update.message.reply_text("لطفاً یک عکس معتبر ارسال کنید.")
        return PHOTO

# حالت در انتظار
async def pending_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اطلاعات شما در حال بررسی می‌باشد، لطفا شکیبا باشید."
    )

# ارسال تایید یا رد به کاربر
async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    if not user_input.startswith("تایید") and not user_input.startswith("رد"):
        await update.message.reply_text("لطفاً فقط 'تایید' یا 'رد' ارسال کنید.")
        return

    try:
        user_id, decision = user_input.split(maxsplit=1)
        user_id = int(user_id)
        if user_id in user_requests:
            if decision == "تایید":
                await context.bot.send_message(
                    chat_id=user_id,
                    text="درخواست شما تأیید شد. لینک گروه: https://t.me/YOUR_GROUP_LINK"
                )
            elif decision == "رد":
                await context.bot.send_message(
                    chat_id=user_id,
                    text="کاربر عزیز اطلاعات شما به درستی و صحت نبود، لطفاً مجدداً با زدن دکمه استارت اطلاعات صحیح خودتون رو ارسال کنید."
                )
            del user_requests[user_id]
        else:
            await update.message.reply_text("کاربر موردنظر یافت نشد.")
    except ValueError:
        await update.message.reply_text("فرمت پیام نادرست است. لطفاً به شکل 'آی‌دی تایید/رد' ارسال کنید.")

# نمایش درخواست‌های در انتظار به مدیر
async def show_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_requests:
        await update.message.reply_text("هیچ درخواستی در حال انتظار نیست.")
        return

    message = "لیست درخواست‌های در انتظار:\n"
    for user_id, details in user_requests.items():
        if details["status"] == "pending":
            message += f"آی‌دی: {user_id}, شماره: {details['phone_number']}\n"
    await update.message.reply_text(message)

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
            PENDING: [MessageHandler(filters.TEXT & ~filters.COMMAND, pending_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("admin_requests", show_requests))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_response))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    import asyncio
    asyncio.run(remove_webhook())
    main()

import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler


BOT_TOKEN = os.getenv('BOT_TOKEN')  # توکن ربات از متغیر محیطی
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # آی‌دی مدیر از متغیر محیطی


PHONE, PHOTO, PENDING = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[KeyboardButton("ارسال شماره تلفن", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "جهت ورود به گروه مهندسی کامپیوتر لطفا مراحل احراز را انجام دهید:",
        reply_markup=reply_markup
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone_number = update.message.contact.phone_number
        context.user_data['phone_number'] = phone_number
        context.user_data['user_chat_id'] = update.effective_user.id
        await update.message.reply_text(
            "در ادامه لطفا اسکرین شات از پروفایل آموزشیار خودتون بفرستید، از مسیر ثبت نام دروس دانشجو > مشاهده وضعیت:"
        )
        return PHOTO
    else:
        await update.message.reply_text(
            "شماره تلفن ارسال نشد. لطفاً دوباره تلاش کنید."
        )
        return PHONE


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file = update.message.photo[-1].file_id
        context.user_data['photo_file'] = photo_file

        await update.message.reply_text(
            "عکس شما دریافت شد. درخواست شما به مدیر ارسال شد."
        )


        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_file,
            caption=f"کاربر {update.effective_user.first_name} با شماره {context.user_data['phone_number']} درخواست عضویت داده است."
        )

        return PENDING
    else:
        await update.message.reply_text("لطفاً یک عکس معتبر ارسال کنید.")
        return PHOTO


async def pending_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اطلاعات شما در حال بررسی می‌باشد، لطفا شکیبا باشید."
    )


async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    user_chat_id = context.user_data.get('user_chat_id')

    if user_input == "تایید":
        await context.bot.send_message(
            chat_id=user_chat_id,
            text="درخواست شما تأیید شد. لینک گروه: https://t.me/YOUR_GROUP_LINK"
        )
    elif user_input == "رد":
        await context.bot.send_message(
            chat_id=user_chat_id,
            text="کاربر عزیز اطلاعات شما به درستی و صحت نبود، لطفاً مجدداً با زدن دکمه استارت اطلاعات صحیح خودتون رو ارسال کنید."
        )
    else:
        await update.message.reply_text("لطفاً فقط 'تایید' یا 'رد' ارسال کنید.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فرآیند لغو شد.")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()


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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_response))
    application.run_polling()

if __name__ == '__main__':
    main()

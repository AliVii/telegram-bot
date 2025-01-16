# استفاده از تصویر رسمی Python
FROM python:3.9-slim

# تنظیم دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی کردن تمام فایل‌های پروژه به داخل کانتینر
COPY . /app

# نصب کتابخانه‌های موردنیاز
RUN pip install --no-cache-dir -r requirements.txt

# اجرای فایل اصلی پروژه
CMD ["python", "bot.py"]

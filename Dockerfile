# استخدام الصورة الرسمية من مايكروسوفت التي تحتوي على بايثون والمتصفحات مسبقاً
FROM mcr.microsoft.com/playwright/python:v1.41.2-jammy

# تحديد مسار العمل داخل السيرفر
WORKDIR /app

# نسخ ملف المكتبات أولاً
COPY requirements.txt .

# تثبيت مكتبات بايثون (تليجرام وطلبات الويب)
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت (مثل main.py)
COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]

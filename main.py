import time
import threading
import os
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- إعدادات البيئة والتوكن (يجب وضعها في المتغيرات في Railway أو الخادم) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "643309456")) # ضع الايدي في المتغيرات
SMS_API_KEY = os.environ.get("SMS_API_KEY", "3jdatCdMpWM5NAE5JWJ64T71uEAGRXpW") # ضع الـ API في المتغيرات

BASE_URL = "https://smsbower.page/stubs/handler_api.php"

# إعداد البروكسي الخاص بك
PROXY_SERVER = "http://a2554925de14dc8880af:b48bdda8a174e3aa@gw.dataimpulse.com:823"

bot = telebot.TeleBot(BOT_TOKEN)

# دالة للتحقق من أن المستخدم هو الآدمن
def is_admin(user_id):
    return user_id == ALLOWED_USER_ID

# --- دالة التقاط الصورة باستخدام Playwright مع البروكسي وتخطي الحماية ---
def take_screenshot_with_proxy(target_url, max_retries=5):
    for attempt in range(1, max_retries + 1):
        print(f"🔄 المحاولة {attempt}: جاري الاتصال بالبروكسي (المهلة 12 ثانية)...")
        try:
            with sync_playwright() as p:
                # تشغيل المتصفح المخفي مع إضافة خصائص لتخطي كشف البوتات
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER},
                    args=['--disable-blink-features=AutomationControlled'] # إخفاء أن المتصفح آلي
                )
                
                # تحديد حجم الشاشة وإضافة User-Agent حقيقي لمتصفح كروم
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = context.new_page()
                
                # الذهاب إلى الرابط والانتظار (المهلة: 12000 مللي ثانية أي 12 ثانية)
                # استخدام "load" بدلاً من "networkidle" يمنع التعليق المستمر
                page.goto(target_url, timeout=12000, wait_until="load")
                
                # 🛑 مهم جداً: إجبار البوت على الانتظار 3 ثوانٍ إضافية لضمان تحميل صفحة نتفلكس بالكامل
                page.wait_for_timeout(3000)
                
                # التقاط صورة للشاشة
                screenshot_bytes = page.screenshot(full_page=True)
                
                browser.close()
                print(f"✅ نجحت المحاولة {attempt} وتم التقاط الصورة.")
                return screenshot_bytes
                
        except PlaywrightTimeoutError:
            print(f"⚠️ تأخر الرد في المحاولة {attempt} (أكثر من 12 ثانية). جاري تبديل الـ IP...")
            time.sleep(1) # استراحة قصيرة قبل المحاولة التالية لضمان الحصول على IP جديد
        except Exception as e:
            print(f"❌ حدث خطأ في المحاولة {attempt}: {e}")
            time.sleep(1)
            
    print("❌ استنفدت جميع المحاولات لفشل البروكسي.")
    return None

# --- لوحة المفاتيح الرئيسية ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    btn_screenshot = InlineKeyboardButton("📸 الدخول إلى الرابط (Clear Cookies)", callback_data="take_screenshot")
    
    markup.add(btn_change_netflix, btn_toggle_logout, btn_screenshot)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "عذراً، هذا البوت مخصص لأشخاص محددين فقط ❌")
        return

    bot.send_message(
        message.chat.id,
        f"مرحباً بك في لوحة تحكم الإدارة ⚙️\n\nاختر الإجراء الذي تريده من القائمة أدناه:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "هذا البوت ليس مخصصاً لك!", show_alert=True)
        return

    # --- زر الدخول للرابط والتقاط الصورة ---
    if call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري المعالجة...")
        bot.edit_message_text(
            "⏳ جارٍ العمل... جاري الاتصال بالبروكسي (قد يستغرق بضع محاولات لضمان اتصال سريع)...",
            chat_id, 
            call.message.message_id
        )
        
        def process_screenshot():
            # تم تعديل الرابط ليكون https://www للحصول على استجابة صحيحة
            url = "https://www.netflix.com/clearcookies"
            photo_bytes = take_screenshot_with_proxy(url)
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(chat_id, photo_bytes, caption="✅ تم الدخول إلى الرابط بنجاح.")
                bot.send_message(chat_id, "القائمة الرئيسية:", reply_markup=main_keyboard())
            else:
                bot.edit_message_text(
                    "❌ حدث خطأ أثناء محاولة فتح الرابط أو البروكسي لا يستجيب.\nالرجاء المحاولة مرة أخرى.",
                    chat_id, 
                    call.message.message_id,
                    reply_markup=main_keyboard()
                )
                
        threading.Thread(target=process_screenshot).start()

    # --- الأزرار الأخرى ---
    elif call.data == "change_netflix_pass":
        bot.answer_callback_query(call.id, "جاري تحضير الأتمتة...")
        bot.edit_message_text(
            "⏳ جارٍ العمل...",
            chat_id, 
            call.message.message_id
        )
        # مساحة لكود تغيير الرمز...

    elif call.data == "toggle_logout":
        bot.answer_callback_query(call.id, "تم تغيير حالة تسجيل الخروج", show_alert=False)

print("البوت يعمل الآن...")
bot.infinity_polling()

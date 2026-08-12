import time
import threading
import os
import shutil
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- إعدادات البيئة والتوكن ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "643309456"))
SMS_API_KEY = os.environ.get("SMS_API_KEY", "3jdatCdMpWM5NAE5JWJ64T71uEAGRXpW")

BASE_URL = "https://smsbower.page/stubs/handler_api.php"

# إعداد البروكسي
PROXY_SERVER = "http://gw.dataimpulse.com:823"
PROXY_USERNAME = "a2554925de14dc8880af"
PROXY_PASSWORD = "b48bdda8a174e3aa"

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return user_id == ALLOWED_USER_ID

# 🔹 متغير عام لحفظ حالة الصفحة المثبتة والمنعزلة 🔹
USER_STATE = {
    "is_pinned": False,
    "pinned_file": "pinned_session.json",
    "temp_file": "temp_session.json"
}

# --- دالة التقاط الصورة باستخدام Playwright (مع ميزة عزل الجلسات) ---
def take_screenshot_with_proxy(target_url, session_file=None, max_retries=5):
    last_error = ""
    for attempt in range(1, max_retries + 1):
        print(f"🔄 المحاولة {attempt}: جاري الاتصال بالبروكسي (المهلة 20 ثانية)...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={
                        "server": PROXY_SERVER,
                        "username": PROXY_USERNAME,
                        "password": PROXY_PASSWORD
                    },
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context_options = {
                    'viewport': {'width': 1280, 'height': 720},
                    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # تحميل الجلسة المنعزلة إذا كانت موجودة
                if session_file and os.path.exists(session_file):
                    context_options['storage_state'] = session_file
                
                context = browser.new_context(**context_options)
                page = context.new_page()
                
                page.goto(target_url, timeout=20000, wait_until="load")
                page.wait_for_timeout(3000)
                
                screenshot_bytes = page.screenshot(full_page=True)
                
                # حفظ حالة الصفحة قبل الإغلاق لتبقى منعزلة ومثبتة
                if session_file:
                    context.storage_state(path=session_file)
                    
                browser.close()
                return screenshot_bytes, "Success"
                
        except PlaywrightTimeoutError:
            last_error = "تأخر الرد لأكثر من 20 ثانية (Timeout)."
            print(f"⚠️ {last_error} - جاري تبديل الـ IP...")
            time.sleep(1)
        except Exception as e:
            last_error = str(e)
            print(f"❌ خطأ في المحاولة {attempt}: {last_error}")
            time.sleep(1)
            
    return None, last_error

# --- لوحة المفاتيح الرئيسية ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    
    # تغيير شكل القائمة بناءً على ما إذا كانت هناك صفحة مثبتة أم لا
    if USER_STATE["is_pinned"]:
        btn_screenshot_new = InlineKeyboardButton("📸 فتح صفحة جديدة (منفصلة)", callback_data="take_screenshot")
        btn_screenshot_pinned = InlineKeyboardButton("📌 عرض الصفحة المثبتة", callback_data="view_pinned_page")
        markup.add(btn_change_netflix, btn_toggle_logout, btn_screenshot_new, btn_screenshot_pinned)
    else:
        btn_screenshot = InlineKeyboardButton("📸 الدخول إلى الرابط (Clear Cookies)", callback_data="take_screenshot")
        markup.add(btn_change_netflix, btn_toggle_logout, btn_screenshot)
        
    return markup

# --- أزرار التحكم تحت الصورة (تثبيت / إلغاء التثبيت) ---
def photo_keyboard(is_viewing_pinned=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    if not is_viewing_pinned:
        markup.add(InlineKeyboardButton("📌 تثبيت هذه الصفحة (عزل)", callback_data="pin_page"))
    else:
        markup.add(InlineKeyboardButton("🔓 إلغاء تثبيت الصفحة", callback_data="unpin_page"))
        
    markup.add(InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "عذراً، هذا البوت مخصص لأشخاص محددين فقط ❌")
        return
    bot.send_message(
        message.chat.id,
        "مرحباً بك في لوحة تحكم الإدارة ⚙️\n\nاختر الإجراء الذي تريده من القائمة أدناه:",
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

    # --- 1. فتح صفحة جديدة ---
    if call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري فتح صفحة جديدة...")
        bot.edit_message_text(
            "⏳ جارٍ العمل... جاري فتح صفحة جديدة تماماً...",
            chat_id, 
            call.message.message_id
        )
        
        def process_screenshot():
            url = "https://www.netflix.com/clearcookies"
            
            # مسح الجلسة المؤقتة السابقة لضمان أن هذه الصفحة جديدة ومنعزلة
            if os.path.exists(USER_STATE["temp_file"]):
                os.remove(USER_STATE["temp_file"])
                
            photo_bytes, error_msg = take_screenshot_with_proxy(url, session_file=USER_STATE["temp_file"])
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(
                    chat_id, 
                    photo_bytes, 
                    caption="✅ تم الدخول إلى الرابط في صفحة جديدة.\n\nهل تريد تثبيتها وعزلها؟",
                    reply_markup=photo_keyboard(is_viewing_pinned=False)
                )
            else:
                bot.edit_message_text(f"❌ فشل الاتصال:\n`{error_msg}`", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")
                
        threading.Thread(target=process_screenshot).start()

    # --- 2. عرض الصفحة المثبتة ---
    elif call.data == "view_pinned_page":
        bot.answer_callback_query(call.id, "جاري الدخول للصفحة المثبتة...")
        bot.edit_message_text("⏳ جارٍ العمل... جاري استرجاع الصفحة المثبتة...", chat_id, call.message.message_id)
        
        def process_pinned():
            url = "https://www.netflix.com/clearcookies"
            # استخدام ملف الجلسة المثبتة
            photo_bytes, error_msg = take_screenshot_with_proxy(url, session_file=USER_STATE["pinned_file"])
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(
                    chat_id, 
                    photo_bytes, 
                    caption="📌 هذه هي صفحتك المثبتة والمنعزلة عن باقي الصفحات.",
                    reply_markup=photo_keyboard(is_viewing_pinned=True)
                )
            else:
                bot.edit_message_text(f"❌ فشل الاتصال بالصفحة المثبتة:\n`{error_msg}`", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")
                
        threading.Thread(target=process_pinned).start()

    # --- 3. زر التثبيت ---
    elif call.data == "pin_page":
        USER_STATE["is_pinned"] = True
        # نقل الكوكيز من الجلسة المؤقتة إلى الجلسة المثبتة
        if os.path.exists(USER_STATE["temp_file"]):
            shutil.copy(USER_STATE["temp_file"], USER_STATE["pinned_file"])
            
        bot.answer_callback_query(call.id, "✅ تم التثبيت! الصفحة الآن منعزلة ومحفوظة.")
        # تغيير الأزرار تحت الصورة لتظهر (إلغاء التثبيت)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=photo_keyboard(is_viewing_pinned=True))

    # --- 4. زر إلغاء التثبيت ---
    elif call.data == "unpin_page":
        USER_STATE["is_pinned"] = False
        # حذف ملف الصفحة المثبتة
        if os.path.exists(USER_STATE["pinned_file"]):
            os.remove(USER_STATE["pinned_file"])
            
        bot.answer_callback_query(call.id, "🔓 تم إلغاء التثبيت وحذف الصفحة المنعزلة.")
        # تغيير الأزرار تحت الصورة لتظهر (تثبيت)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=photo_keyboard(is_viewing_pinned=False))

    # --- 5. زر الرجوع للقائمة الرئيسية ---
    elif call.data == "back_to_main":
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "مرحباً بك في القائمة الرئيسية:", reply_markup=main_keyboard())

    # --- الأزرار الأخرى ---
    elif call.data == "change_netflix_pass":
        bot.answer_callback_query(call.id, "جاري تحضير الأتمتة...")
        bot.edit_message_text("⏳ جارٍ العمل...", chat_id, call.message.message_id)

    elif call.data == "toggle_logout":
        bot.answer_callback_query(call.id, "تم تغيير حالة تسجيل الخروج", show_alert=False)

print("البوت يعمل الآن...")
bot.infinity_polling()

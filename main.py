import time
import threading
import os
import shutil
import random
import string
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

# 🔹 متغير عام لحفظ حالة الصفحة المثبتة، وملفاتها، وطول الإيميل 🔹
USER_STATE = {
    "is_pinned": False,
    "pinned_session": "pinned_session.json",
    "pinned_image": "pinned_image.png",
    "temp_session": "temp_session.json",
    "temp_image": "temp_image.png",
    "email_length": 5  # طول الأحرف العشوائية الافتراضي
}

# --- دالة توليد الإيميل العشوائي ---
def generate_random_email(length):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{username}@5xu.vn"

# --- دالة التقاط الصورة العادية ---
def take_screenshot_with_proxy(target_url, session_file=None, image_file=None, max_retries=5):
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context_options = {
                    'viewport': {'width': 1280, 'height': 720},
                    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                if session_file and os.path.exists(session_file):
                    context_options['storage_state'] = session_file
                
                context = browser.new_context(**context_options)
                page = context.new_page()
                
                page.goto(target_url, timeout=20000, wait_until="load")
                page.wait_for_timeout(3000)
                
                screenshot_bytes = page.screenshot(full_page=True)
                
                if session_file:
                    context.storage_state(path=session_file)
                
                if image_file:
                    with open(image_file, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                browser.close()
                return screenshot_bytes, "Success"
                
        except PlaywrightTimeoutError:
            last_error = "تأخر الرد لأكثر من 20 ثانية (Timeout)."
            time.sleep(1)
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
            
    return None, last_error

# --- دالة أتمتة التسجيل (مع التقاط صورة عند الخطأ) ---
def execute_netflix_automation(session_file, image_file, email):
    current_page = None # لتتبع الصفحة الحالية لالتقاط صورة لها عند الخطأ
    error_screenshot_path = "error_screenshot.png"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                storage_state=session_file if os.path.exists(session_file) else None,
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            # --- 1. التعامل مع نتفلكس ---
            netflix_page = context.new_page()
            current_page = netflix_page # تعيين الصفحة الحالية لتصويرها إذا حدث خطأ
            
            netflix_page.goto("https://www.netflix.com/", timeout=20000, wait_until="load")
            netflix_page.wait_for_timeout(3000)
            
            # كتابة الإيميل
            netflix_page.get_by_placeholder("Email address").fill(email)
            
            # الضغط على زر Try 30 Days
            try:
                netflix_page.locator(':is(button, a):has-text("Try 30 Days for USD 0")').first.click(timeout=5000)
            except:
                # محاولة بديلة إذا كان شكل الزر مختلفاً
                netflix_page.locator("button[type='submit']").first.click(timeout=5000)
                
            netflix_page.wait_for_timeout(4000) # انتظار تحميل الصفحة التالية
            
            # الضغط على زر التالي / Next (اختياري، نتخطاه إذا لم يظهر)
            try:
                next_btn = netflix_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي")').first
                if next_btn.is_visible():
                    next_btn.click(timeout=5000)
                    netflix_page.wait_for_timeout(4000)
            except Exception:
                pass
                
            # حفظ الجلسة الجديدة والصورة لتبقى الصفحة المثبتة محدثة
            context.storage_state(path=session_file)
            netflix_page.screenshot(path=image_file, full_page=True)
            
            # --- 2. فتح موقع البريد لاستخراج الرسائل ---
            email_page = context.new_page()
            current_page = email_page # تغيير التتبع إلى صفحة البريد
            
            email_page.goto(f"https://generator.email/inbox9/{email}", timeout=30000, wait_until="load")
            
            # إعطاء الموقع 8 ثوانٍ لاستلام الرسالة
            email_page.wait_for_timeout(8000)
            
            # استخراج جميع الروابط من صفحة البريد
            links = email_page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map(a => a.href);
            }""")
            
            # تصفية الروابط للحصول على روابط نتفلكس فقط
            netflix_links = list(set([l for l in links if 'netflix.com' in l and 'nflx' not in l]))
            
            # استخراج جزء من النص البريدي
            try:
                text_content = email_page.locator("body").inner_text()
                extracted_text = text_content[:500] + "..." # نأخذ أول 500 حرف لتجنب رسائل تليجرام الطويلة
            except:
                extracted_text = "تعذر استخراج النص المباشر، الرجاء فحص الروابط."

            browser.close()
            return True, {"links": netflix_links, "text": extracted_text}
            
    except Exception as e:
        # 🛑 التقاط صورة لحظة حدوث الخطأ 🛑
        captured_path = None
        if current_page:
            try:
                current_page.screenshot(path=error_screenshot_path, full_page=True)
                captured_path = error_screenshot_path
            except:
                pass
        return False, {"error": str(e), "screenshot": captured_path}

# --- لوحة المفاتيح الرئيسية ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    
    if USER_STATE["is_pinned"]:
        btn_screenshot_new = InlineKeyboardButton("📸 فتح صفحة جديدة (منفصلة)", callback_data="take_screenshot")
        btn_screenshot_pinned = InlineKeyboardButton("📌 عرض الصفحة المثبتة", callback_data="view_pinned_page")
        
        # أزرار الأتمتة للإيميل
        btn_auto = InlineKeyboardButton("🚀 بدء التسجيل (إدخال الإيميل)", callback_data="start_auto")
        btn_length_info = InlineKeyboardButton(f"طول الإيميل: {USER_STATE['email_length']}", callback_data="none")
        btn_plus = InlineKeyboardButton("➕ زيادة", callback_data="inc_email")
        btn_minus = InlineKeyboardButton("➖ تقليل", callback_data="dec_email")
        
        markup.add(btn_change_netflix, btn_toggle_logout)
        markup.add(btn_screenshot_new, btn_screenshot_pinned)
        markup.add(btn_auto)
        markup.row(btn_minus, btn_length_info, btn_plus)
    else:
        btn_screenshot = InlineKeyboardButton("📸 الدخول إلى الرابط (Clear Cookies)", callback_data="take_screenshot")
        markup.add(btn_change_netflix, btn_toggle_logout, btn_screenshot)
        
    return markup

# --- أزرار التحكم تحت الصورة ---
def photo_keyboard(is_viewing_pinned=False):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    if not is_viewing_pinned:
        markup.add(InlineKeyboardButton("📌 تثبيت وعزل هذه الصفحة", callback_data="pin_page"))
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
        f"مرحباً بك يا نبيل في لوحة تحكم الإدارة ⚙️\n\nاختر الإجراء الذي تريده من القائمة أدناه:",
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

    # --- التحكم بطول الإيميل ---
    if call.data == "inc_email":
        if USER_STATE["email_length"] < 15:
            USER_STATE["email_length"] += 1
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=main_keyboard())
        return
        
    elif call.data == "dec_email":
        if USER_STATE["email_length"] > 4:
            USER_STATE["email_length"] -= 1
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=main_keyboard())
        return

    # --- زر بدء التسجيل والأتمتة ---
    elif call.data == "start_auto":
        target_email = generate_random_email(USER_STATE['email_length'])
        
        bot.answer_callback_query(call.id, "جاري بدء الأتمتة...")
        bot.edit_message_text(
            f"⏳ يتم الآن العمل على الإيميل:\n`{target_email}`\n\n- إدخال الإيميل...\n- تخطي الصفحات...\n- فحص البريد الوارد...\nالرجاء الانتظار (قد يستغرق 20-30 ثانية).",
            chat_id, 
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        def run_automation():
            success, result = execute_netflix_automation(USER_STATE["pinned_session"], USER_STATE["pinned_image"], target_email)
            
            bot.delete_message(chat_id, call.message.message_id)
            
            if success:
                if os.path.exists(USER_STATE["pinned_image"]):
                    with open(USER_STATE["pinned_image"], "rb") as img:
                        bot.send_photo(chat_id, img, caption="📸 صورة نتفلكس بعد إدخال الإيميل وتخطي الصفحة:")
                
                links_text = "\n".join(result["links"]) if result["links"] else "⚠️ لم يتم العثور على روابط نتفلكس في الرسالة."
                msg = (f"✅ **اكتملت الأتمتة بنجاح!**\n\n"
                       f"📧 **الإيميل:** `{target_email}`\n\n"
                       f"🔗 **الروابط المستخرجة:**\n{links_text}\n\n"
                       f"📄 **محتوى من البريد:**\n`{result['text']}`")
                       
                bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=main_keyboard())
            else:
                # 🛑 معالجة الخطأ وإرسال الصورة 🛑
                error_msg = result.get("error", "Unknown Error")
                screenshot_path = result.get("screenshot")
                
                caption = f"❌ حدث خطأ أثناء الأتمتة:\n`{error_msg}`\n\nهذه صورة للصفحة لحظة توقف البوت لمعرفة السبب 👇"
                
                if screenshot_path and os.path.exists(screenshot_path):
                    with open(screenshot_path, "rb") as img:
                        bot.send_photo(chat_id, img, caption=caption, parse_mode="Markdown", reply_markup=main_keyboard())
                    os.remove(screenshot_path) # تنظيف الصورة بعد إرسالها
                else:
                    bot.send_message(chat_id, caption, reply_markup=main_keyboard(), parse_mode="Markdown")

        threading.Thread(target=run_automation).start()

    # --- فتح صفحة جديدة ---
    elif call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري فتح صفحة جديدة...")
        bot.edit_message_text("⏳ جارٍ العمل... جاري فتح صفحة جديدة والاتصال بالبروكسي...", chat_id, call.message.message_id)
        
        def process_screenshot():
            url = "https://www.netflix.com/clearcookies"
            for file_name in [USER_STATE["temp_session"], USER_STATE["temp_image"]]:
                if os.path.exists(file_name):
                    os.remove(file_name)
                
            photo_bytes, error_msg = take_screenshot_with_proxy(url, session_file=USER_STATE["temp_session"], image_file=USER_STATE["temp_image"])
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(chat_id, photo_bytes, caption="✅ تم الدخول إلى الرابط.\n\nهل تريد تثبيتها (تجميدها) للرجوع إليها لاحقاً؟", reply_markup=photo_keyboard(is_viewing_pinned=False))
            else:
                bot.edit_message_text(f"❌ فشل الاتصال:\n`{error_msg}`", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")
                
        threading.Thread(target=process_screenshot).start()

    # --- عرض الصفحة المثبتة ---
    elif call.data == "view_pinned_page":
        bot.answer_callback_query(call.id, "جاري العرض...")
        if os.path.exists(USER_STATE["pinned_image"]):
            with open(USER_STATE["pinned_image"], 'rb') as img_file:
                photo_bytes = img_file.read()
                
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_photo(chat_id, photo_bytes, caption="📌 عرض الصفحة المثبتة (نسخة مجمدة ثابتة).", reply_markup=photo_keyboard(is_viewing_pinned=True))
        else:
            bot.edit_message_text("❌ لم يتم العثور على صورة مثبتة.", chat_id, call.message.message_id, reply_markup=main_keyboard())

    # --- تثبيت الصفحة ---
    elif call.data == "pin_page":
        USER_STATE["is_pinned"] = True
        if os.path.exists(USER_STATE["temp_session"]):
            shutil.copy(USER_STATE["temp_session"], USER_STATE["pinned_session"])
        if os.path.exists(USER_STATE["temp_image"]):
            shutil.copy(USER_STATE["temp_image"], USER_STATE["pinned_image"])
            
        bot.answer_callback_query(call.id, "✅ تم تجميد وتثبيت الصفحة بنجاح!")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=photo_keyboard(is_viewing_pinned=True))

    # --- إلغاء التثبيت ---
    elif call.data == "unpin_page":
        USER_STATE["is_pinned"] = False
        for file_name in [USER_STATE["pinned_session"], USER_STATE["pinned_image"]]:
            if os.path.exists(file_name):
                os.remove(file_name)
            
        bot.answer_callback_query(call.id, "🔓 تم إلغاء التثبيت وحذف الصفحة المنعزلة.")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=photo_keyboard(is_viewing_pinned=False))

    # --- زر الرجوع ---
    elif call.data == "back_to_main":
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "مرحباً بك في القائمة الرئيسية:", reply_markup=main_keyboard())

print("البوت يعمل الآن...")
bot.infinity_polling()

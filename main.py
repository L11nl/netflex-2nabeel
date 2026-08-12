import time
import threading
import os
import shutil
import random
import string
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.sync_api import sync_playwright

# محاولة استدعاء مكتبة التخفي
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

# --- إعدادات البيئة والتوكن ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "643309456"))

# إعداد البروكسي
PROXY_SERVER = "http://gw.dataimpulse.com:823"
PROXY_USERNAME = "a2554925de14dc8880af"
PROXY_PASSWORD = "b48bdda8a174e3aa"

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return user_id == ALLOWED_USER_ID

USER_STATE = {
    "is_pinned": False,
    "pinned_session": "pinned_session.json",
    "pinned_image": "pinned_image.png",
    "temp_session": "temp_session.json",
    "temp_image": "temp_image.png",
    "email_length": 5  
}

def generate_random_email(length):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{username}@5xu.vn"

def apply_stealth(page):
    if stealth_sync:
        stealth_sync(page)
    else:
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def safely_goto(page, url, timeout=40000):
    """دالة عبقرية لتخطي خطأ الـ Timeout: تفتح الرابط، وإذا تأخرت السكربتات الإعلانية، تتجاهلها وتكمل العمل"""
    try:
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    except Exception:
        pass # نتجاهل خطأ التحميل لأن الصفحة غالباً تكون قد ظهرت بالفعل
    page.wait_for_timeout(3000)

def send_progress_photo(page, chat_id, caption):
    try:
        page.wait_for_timeout(1000) 
        screenshot_bytes = page.screenshot(full_page=False, timeout=15000)
        bot.send_photo(chat_id, screenshot_bytes, caption=caption)
    except Exception:
        bot.send_message(chat_id, f"{caption}\n\n*(⚠️ مستمرون في العمل بالرغم من تعذر التصوير...)*", parse_mode="Markdown")

# --- دالة التقاط الصورة (مضادة للانهيار) ---
def take_screenshot_with_proxy(target_url, session_file=None, image_file=None, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                
                context_options = {
                    'viewport': {'width': 1280, 'height': 720},
                    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                if session_file and os.path.exists(session_file):
                    context_options['storage_state'] = session_file
                
                context = browser.new_context(**context_options)
                page = context.new_page()
                apply_stealth(page) 
                
                # استخدام الدالة الآمنة لتخطي الـ Timeout
                safely_goto(page, target_url)
                
                screenshot_bytes = page.screenshot(full_page=False, timeout=20000)
                
                if session_file:
                    context.storage_state(path=session_file)
                if image_file:
                    with open(image_file, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                browser.close()
                return screenshot_bytes, "Success"
        except Exception as e:
            time.sleep(2)
            
    return None, "فشل الاتصال بالبروكسي تماماً."

# --- دالة أتمتة التسجيل (نظام الاستراتيجيات المتعددة) ---
def execute_netflix_automation(session_file, image_file, email, chat_id):
    strategies = [
        {"name": "الاستراتيجية 1 (صفحة Log in العادية)", "url": "https://www.netflix.com/login", "is_mobile": False},
        {"name": "الاستراتيجية 2 (الصفحة الرئيسية Home)", "url": "https://www.netflix.com/", "is_mobile": False},
        {"name": "الاستراتيجية 3 (محاكاة هاتف iPhone)", "url": "https://www.netflix.com/", "is_mobile": True}
    ]
    
    success = False
    
    for strategy in strategies:
        bot.send_message(chat_id, f"🔄 **جاري تجربة: {strategy['name']}**", parse_mode="Markdown")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                
                # إعدادات السياق (كمبيوتر أو هاتف بناءً على الاستراتيجية)
                if strategy["is_mobile"]:
                    context_options = {
                        'viewport': {'width': 375, 'height': 812},
                        'user_agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                        'is_mobile': True,
                        'has_touch': True
                    }
                else:
                    context_options = {
                        'viewport': {'width': 1280, 'height': 720},
                        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                    
                context = browser.new_context(**context_options)
                netflix_page = context.new_page()
                apply_stealth(netflix_page)
                
                # 1. فتح الصفحة بأمان
                safely_goto(netflix_page, strategy["url"])
                send_progress_photo(netflix_page, chat_id, "📸 الصفحة بعد الفتح.")
                
                # 2. إدخال الإيميل
                try:
                    email_input = netflix_page.locator("input[name='email'], input[name='userLoginId'], input[type='email']").first
                    if email_input.is_visible(timeout=5000):
                        email_input.click()
                        email_input.fill("")
                        for char in email:
                            email_input.press_sequentially(char, delay=random.randint(50, 200))
                        netflix_page.wait_for_timeout(1000)
                except:
                    pass
                
                # 3. الضغط على أزرار المتابعة
                try:
                    continue_btn = netflix_page.locator(':is(button, a):has-text("Continue"), :is(button, a):has-text("Next"), :is(button, a):has-text("متابعة"), :is(button, a):has-text("التالي"), :is(button, a):has-text("Get Started"), :is(button, a):has-text("Days for USD 0")').first
                    if continue_btn.is_visible(timeout=3000):
                        continue_btn.click(timeout=10000)
                    else:
                        email_input.press("Enter")
                except:
                    try: email_input.press("Enter")
                    except: pass
                    
                netflix_page.wait_for_timeout(7000)
                send_progress_photo(netflix_page, chat_id, "📸 الصفحة بعد ضغط الاستمرار.")
                
                # 4. فحص الخطأ الأحمر (إذا وجدناه، نكسر هذه الاستراتيجية لننتقل للتي بعدها)
                try:
                    error_msg = netflix_page.locator('text="Something went wrong"').first
                    if error_msg.is_visible(timeout=3000):
                        bot.send_message(chat_id, "⚠️ ظهر الخطأ الأحمر (حظر ريكابتشا). سننتقل للاستراتيجية البديلة فوراً...")
                        browser.close()
                        continue # ينتقل للاستراتيجية التالية في الحلقة (For)
                except:
                    pass
                    
                # 5. إذا لم يظهر الخطأ، نبحث عن Resend Link
                for i in range(1, 4):
                    try:
                        resend_btn = netflix_page.locator(':is(button, a):has-text("Resend Link"), :is(button, a):has-text("إعادة إرسال")').first
                        if resend_btn.is_visible(timeout=3000):
                            bot.send_message(chat_id, f"✅ نجحت {strategy['name']}! تم الوصول لصفحة الإرسال.")
                            success = True
                            break
                            
                        # إعادة إدخال الإيميل إن طُلب
                        try:
                            email_input_again = netflix_page.locator("input[name='email'], input[name='userLoginId'], input[type='email']").first
                            if email_input_again.is_visible(timeout=2000) and not email_input_again.input_value():
                                email_input_again.click()
                                email_input_again.type(email, delay=100)
                                netflix_page.wait_for_timeout(1000)
                        except: pass
                        
                        next_btn = netflix_page.locator(':is(button, a):has-text("Send Link"), :is(button, a):has-text("إرسال الرابط"), :is(button, a):has-text("Next"), :is(button, a):has-text("Continue"), :is(button, a):has-text("التالي"), :is(button, a):has-text("متابعة")').first
                        
                        if next_btn.is_visible(timeout=4000):
                            next_btn.click(timeout=10000)
                            netflix_page.wait_for_timeout(6000)
                            send_progress_photo(netflix_page, chat_id, f"📸 تخطي صفحة فرعية...")
                        else:
                            break 
                    except Exception:
                        break
                
                if success:
                    # إذا نجحت الاستراتيجية، نغلق المتصفح ونكسر حلقة الاستراتيجيات الكبيرة للذهاب للبريد
                    browser.close()
                    break
                else:
                    # إذا لم تنجح، نغلق المتصفح ونجرب الاستراتيجية التالية
                    browser.close()
                    
        except Exception as e:
            bot.send_message(chat_id, f"فشلت هذه الاستراتيجية بسبب خطأ برمجي، ننتقل للتي تليها...")

    # --- الخطوة النهائية: صندوق البريد (تُنفذ فقط إذا نجحت إحدى الاستراتيجيات) ---
    if success:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                context = browser.new_context()
                email_page = context.new_page()
                apply_stealth(email_page)
                
                bot.send_message(chat_id, "⏳ ننتقل الآن للبريد الوارد لانتظار الرسالة...")
                safely_goto(email_page, f"https://generator.email/inbox9/{email}", timeout=60000)
                email_page.wait_for_timeout(12000) 
                
                send_progress_photo(email_page, chat_id, "📸 صندوق البريد بعد الانتظار.")
                
                links = email_page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a')).map(a => a.href);
                }""")
                netflix_links = list(set([l for l in links if 'netflix.com' in l and 'nflx' not in l]))
                
                try:
                    text_content = email_page.locator("body").inner_text()
                    extracted_text = text_content[:500] + "..."
                except:
                    extracted_text = "تعذر استخراج النص."

                browser.close()
                return True, {"links": netflix_links, "text": extracted_text}
        except Exception as e:
            return False, f"خطأ في البريد: {str(e)}"
    else:
        return False, "❌ فشلت جميع الاستراتيجيات (1 و 2 و 3) في تجاوز حماية نتفلكس. قد يكون البروكسي محظوراً بالكامل من نتفلكس."

# --- القوائم السفلية والباقي بدون تغيير ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    
    if USER_STATE["is_pinned"]:
        btn_screenshot_new = InlineKeyboardButton("📸 فتح صفحة جديدة (منفصلة)", callback_data="take_screenshot")
        btn_screenshot_pinned = InlineKeyboardButton("📌 عرض الصفحة المثبتة", callback_data="view_pinned_page")
        
        btn_auto = InlineKeyboardButton("🚀 بدء نظام الاستراتيجيات المتعددة", callback_data="start_auto")
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
        return
    bot.send_message(
        message.chat.id,
        "مرحباً بك في لوحة تحكم الإدارة ⚙️\n\nاختر الإجراء الذي تريده:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return

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
    elif call.data == "start_auto":
        target_email = generate_random_email(USER_STATE['email_length'])
        bot.answer_callback_query(call.id, "جاري التنفيذ...")
        bot.delete_message(chat_id, call.message.message_id) 
        
        def run_automation():
            success, result = execute_netflix_automation(USER_STATE["pinned_session"], USER_STATE["pinned_image"], target_email, chat_id)
            
            if success:
                links_text = "\n".join(result["links"]) if result["links"] else "⚠️ لم يتم العثور على روابط نتفلكس."
                msg = f"✅ **تم!**\n\n📧 `{target_email}`\n\n🔗 **الروابط:**\n{links_text}"
                bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=main_keyboard())
            else:
                bot.send_message(chat_id, f"❌ **نتيجة النهاية:**\n`{result}`", reply_markup=main_keyboard(), parse_mode="Markdown")

        threading.Thread(target=run_automation).start()

    elif call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري فتح صفحة جديدة...")
        bot.edit_message_text("⏳ جاري الفتح بقوة (متجاهلاً مهلة الانتظار)...", chat_id, call.message.message_id)
        
        def process_screenshot():
            url = "https://www.netflix.com/clearcookies"
            for file_name in [USER_STATE["temp_session"], USER_STATE["temp_image"]]:
                if os.path.exists(file_name): os.remove(file_name)
                
            photo_bytes, error_msg = take_screenshot_with_proxy(url, session_file=USER_STATE["temp_session"], image_file=USER_STATE["temp_image"])
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(chat_id, photo_bytes, caption="✅ هل تريد التثبيت؟", reply_markup=photo_keyboard(is_viewing_pinned=False))
            else:
                bot.edit_message_text(f"❌ فشل:\n`{error_msg}`", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")
                
        threading.Thread(target=process_screenshot).start()

    elif call.data == "view_pinned_page":
        bot.answer_callback_query(call.id, "جاري العرض...")
        if os.path.exists(USER_STATE["pinned_image"]):
            with open(USER_STATE["pinned_image"], 'rb') as img_file:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(chat_id, img_file.read(), caption="📌 عرض الصفحة المثبتة.", reply_markup=photo_keyboard(is_viewing_pinned=True))
        else:
            bot.edit_message_text("❌ لم يتم العثور على صورة.", chat_id, call.message.message_id, reply_markup=main_keyboard())

    elif call.data == "pin_page":
        USER_STATE["is_pinned"] = True
        if os.path.exists(USER_STATE["temp_session"]): shutil.copy(USER_STATE["temp_session"], USER_STATE["pinned_session"])
        if os.path.exists(USER_STATE["temp_image"]): shutil.copy(USER_STATE["temp_image"], USER_STATE["pinned_image"])
        bot.answer_callback_query(call.id, "✅ تم التثبيت!")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=photo_keyboard(is_viewing_pinned=True))

    elif call.data == "unpin_page":
        USER_STATE["is_pinned"] = False
        for file_name in [USER_STATE["pinned_session"], USER_STATE["pinned_image"]]:
            if os.path.exists(file_name): os.remove(file_name)
        bot.answer_callback_query(call.id, "🔓 تم إلغاء التثبيت.")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=photo_keyboard(is_viewing_pinned=False))

    elif call.data == "back_to_main":
        bot.delete_message(chat_id, call.message.message_id)
        bot.send_message(chat_id, "القائمة الرئيسية:", reply_markup=main_keyboard())

print("البوت يعمل الآن...")
bot.infinity_polling()

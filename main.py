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

# مكتبة التخفي
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

# 🔹 متغيرات حالة المستخدم 🔹
USER_STATE = {
    "is_pinned": False,
    "pinned_session": "pinned_session.json",
    "pinned_image": "pinned_image.png",
    "temp_session": "temp_session.json",
    "temp_image": "temp_image.png",
    "email_length": 5,
    "waiting_for": None, 
    "input_data": None,
    "input_event": threading.Event(),
    "change_phone": False
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
    try:
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    except Exception:
        pass 
    page.wait_for_timeout(3000)

def send_progress_photo(page, chat_id, caption):
    try:
        page.wait_for_timeout(1500) 
        screenshot_bytes = page.screenshot(full_page=False, timeout=15000)
        bot.send_photo(chat_id, screenshot_bytes, caption=caption)
    except Exception as e:
        bot.send_message(chat_id, f"{caption}\n\n*(⚠️ لم نتمكن من التقاط الصورة، مستمرون...)*", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: USER_STATE["waiting_for"] in ["phone", "otp"])
def handle_interactive_input(message):
    if not is_admin(message.from_user.id):
        return
    USER_STATE["input_data"] = message.text.strip()
    USER_STATE["input_event"].set()
    bot.send_message(message.chat.id, "✅ تم استلام الإدخال، جاري تطبيقه في المتصفح الآن...")

def take_screenshot_with_proxy(target_url, session_file=None, image_file=None, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.firefox.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD}
                )
                context_options = {'viewport': {'width': 1280, 'height': 720}, 'ignore_https_errors': True}
                if session_file and os.path.exists(session_file):
                    context_options['storage_state'] = session_file
                
                context = browser.new_context(**context_options)
                page = context.new_page()
                apply_stealth(page) 
                safely_goto(page, target_url)
                screenshot_bytes = page.screenshot(full_page=False, timeout=20000)
                
                if session_file: context.storage_state(path=session_file)
                if image_file:
                    with open(image_file, 'wb') as f: f.write(screenshot_bytes)
                browser.close()
                return screenshot_bytes, "Success"
        except Exception:
            time.sleep(2)
    return None, "فشل الاتصال."

def execute_netflix_automation(session_file, image_file, email, chat_id):
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(
                headless=True,
                proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD}
            )
            
            context_options = {'viewport': {'width': 1280, 'height': 720}, 'ignore_https_errors': True}
            if session_file and os.path.exists(session_file):
                context_options['storage_state'] = session_file
                
            context = browser.new_context(**context_options)
            netflix_page = context.new_page()
            apply_stealth(netflix_page)
            
            # --- الخطوة 1: الفتح ---
            bot.send_message(chat_id, "⏳ جاري تنفيذ المسار الناجح (فايرفوكس المخفي)...")
            safely_goto(netflix_page, "https://www.netflix.com/login")
            send_progress_photo(netflix_page, chat_id, "📸 [1] تم فتح صفحة نتفلكس الرئيسية.")
            
            # --- الخطوة 2: الإيميل ---
            try:
                email_input = netflix_page.locator("input[name='email'], input[name='userLoginId'], input[type='email']").first
                if email_input.is_visible(timeout=5000):
                    email_input.click()
                    email_input.fill("")
                    for char in email:
                        email_input.press_sequentially(char, delay=random.randint(50, 150))
                    netflix_page.wait_for_timeout(1000)
            except:
                pass
            
            try:
                continue_btn = netflix_page.locator(':is(button, a):has-text("Continue"), :is(button, a):has-text("Next"), :is(button, a):has-text("متابعة"), :is(button, a):has-text("التالي"), :is(button, a):has-text("Get Started"), :is(button, a):has-text("Days for USD 0")').first
                if continue_btn.is_visible(timeout=3000):
                    continue_btn.hover()
                    netflix_page.wait_for_timeout(500)
                    continue_btn.click(timeout=10000)
                else:
                    email_input.press("Enter")
            except:
                try: email_input.press("Enter")
                except: pass
                
            netflix_page.wait_for_timeout(7000)
            send_progress_photo(netflix_page, chat_id, "📸 [2] الصفحة بعد إدخال الإيميل.")
            
            try:
                error_msg = netflix_page.locator('text="Something went wrong"').first
                if error_msg.is_visible(timeout=3000):
                    send_progress_photo(netflix_page, chat_id, "📸 [تحذير] ظهر الخطأ الأحمر، جاري التحديث...")
                    netflix_page.reload(timeout=60000, wait_until="domcontentloaded")
                    netflix_page.wait_for_timeout(5000)
            except:
                pass
                
            # --- الخطوة 3: التحقق وتخطي الصفحات ---
            for i in range(1, 5):
                try:
                    success_target = netflix_page.locator(':is(:text("Tap the link in your email")), :is(:text("resend it")), :is(button, a):has-text("Resend Link"), :is(button, a):has-text("إعادة إرسال")').first
                    if success_target.is_visible(timeout=4000):
                        bot.send_message(chat_id, "✅ ممتاز! تم إرسال رسالة إنشاء الحساب بنجاح.")
                        send_progress_photo(netflix_page, chat_id, "📸 [3] صورة صفحة النجاح.")
                        break 
                        
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
                        send_progress_photo(netflix_page, chat_id, f"📸 [تخطي] تم تخطي صفحة فرعية رقم {i}...")
                    else:
                        break 
                except Exception:
                    break
            
            # --- الخطوة 4: صندوق البريد ---
            bot.send_message(chat_id, "⏳ ننتقل للبريد لاستخراج رابط (إكمال التسجيل)...")
            chrome_browser = p.chromium.launch(
                headless=True,
                proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD}
            )
            chrome_context = chrome_browser.new_context()
            email_page = chrome_context.new_page()
            apply_stealth(email_page)
            
            safely_goto(email_page, f"https://generator.email/inbox9/{email}", timeout=60000)
            email_page.wait_for_timeout(12000) 
            send_progress_photo(email_page, chat_id, "📸 [4] صندوق البريد بعد انتظار وصول الرسالة.")
            
            links = email_page.evaluate("""() => { return Array.from(document.querySelectorAll('a')).map(a => a.href); }""")
            netflix_links = list(set([l for l in links if 'netflix.com' in l and 'nflx' not in l]))
            
            epr_link = None
            for link in netflix_links:
                if 'epr' in link or 'code=' in link:
                    epr_link = link
                    break
            
            if not epr_link:
                browser.close()
                chrome_browser.close()
                return True, {"links": netflix_links, "text": "لم يتم العثور على رابط epr."}

            bot.send_message(chat_id, f"🔗 تم إيجاد رابط إكمال التسجيل!\n`{epr_link}`\n\n⏳ جاري فتح الرابط في المتصفح...")
            
            # -------------------------------------------------------------
            # 🔥 المرحلة الثانية: الضغط على Finish Sign-Up وإضافة فاتورة الهاتف 🔥
            # -------------------------------------------------------------
            signup_page = context.new_page()
            apply_stealth(signup_page)
            safely_goto(signup_page, epr_link)
            
            send_progress_photo(signup_page, chat_id, "📸 [5] تم فتح رابط إكمال التسجيل (EPR).")

            # الضغط حصرياً على زر Finish Sign-Up الظاهر في الصورة
            try:
                finish_sign_btn = signup_page.locator('text="Finish Sign-Up"').first
                if finish_sign_btn.is_visible(timeout=10000):
                    finish_sign_btn.click(timeout=10000)
                    signup_page.wait_for_timeout(6000)
                    send_progress_photo(signup_page, chat_id, "📸 [6] تم الضغط على زر (Finish Sign-Up) بنجاح.")
                else:
                    signup_page.locator(':is(button, a):has-text("Finish Sign-Up"), :is(button, a):has-text("Continue")').first.click(timeout=5000)
                    signup_page.wait_for_timeout(5000)
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ محاولة ضغط زر Finish Sign-Up: {e}")

            # تخطي أي صفحة ترحيبية أخرى إن وجدت
            for i in range(1, 3):
                try:
                    next_btn_extra = signup_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي"), :is(button, a):has-text("Continue")').first
                    if next_btn_extra.is_visible(timeout=3000):
                        next_btn_extra.click()
                        signup_page.wait_for_timeout(4000)
                except:
                    break

            send_progress_photo(signup_page, chat_id, "📸 [7] الشاشة الحالية قبل اختيار فاتورة الهاتف.")

            # اختيار فاتورة الهاتف (Add to mobile bill)
            bot.send_message(chat_id, "⏳ جاري اختيار (إضافة إلى فاتورة الهاتف المحمول)...")
            try:
                mobile_bill_option = signup_page.locator('*:has-text("Add to mobile bill"), *:has-text("فاتورة الهاتف"), *:has-text("فاتورة الجوال")').last
                mobile_bill_option.click(timeout=10000)
                signup_page.wait_for_timeout(4000)
                send_progress_photo(signup_page, chat_id, "📸 [8] تم تحديد خيار (فاتورة الهاتف).")
                
                next_btn2 = signup_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي")').first
                if next_btn2.is_visible(timeout=3000):
                    next_btn2.click()
                    signup_page.wait_for_timeout(4000)
                    send_progress_photo(signup_page, chat_id, "📸 [9] تم الضغط على التالي بعد اختيار الوسيلة.")
            except Exception:
                signup_page.keyboard.press("Enter")
                signup_page.wait_for_timeout(3000)

            while True:
                send_progress_photo(signup_page, chat_id, "📸 [10] صفحة إدخال رقم الهاتف جاهزة.")
                
                bot.send_message(chat_id, "📱 **مطلوب رقم الهاتف:**\n\nأرسل رقم الهاتف الآن في رسالة عادية (البوت سينتظرك لمدة 3 دقائق)...", parse_mode="Markdown")
                
                USER_STATE["waiting_for"] = "phone"
                USER_STATE["input_data"] = None
                USER_STATE["input_event"].clear()
                USER_STATE["change_phone"] = False
                
                if not USER_STATE["input_event"].wait(timeout=180):
                    browser.close()
                    chrome_browser.close()
                    return False, "انتهى وقت الانتظار لرقم الهاتف (3 دقائق)."
                    
                phone_num = USER_STATE["input_data"]
                USER_STATE["waiting_for"] = None 
                
                bot.send_message(chat_id, f"⏳ جاري إدخال الرقم `{phone_num}` والموافقة على الشروط...")
                try:
                    phone_input = signup_page.locator('input[type="tel"], input[name="phoneNumber"]').first
                    phone_input.fill(phone_num)
                    signup_page.wait_for_timeout(1000)
                    
                    agree_checkbox = signup_page.locator('input[type="checkbox"]').first
                    agree_checkbox.check(force=True)
                    signup_page.wait_for_timeout(1000)
                    
                    send_progress_photo(signup_page, chat_id, "📸 [11] تم إدخال الرقم وتحديد المربع.")
                    
                    verify_btn = signup_page.locator(':is(button, a):has-text("Verify Phone Number"), :is(button, a):has-text("التحقق")').first
                    verify_btn.click(timeout=10000)
                    signup_page.wait_for_timeout(6000)
                except Exception as e:
                    pass

                send_progress_photo(signup_page, chat_id, "📸 [12] صفحة إدخال الكود (OTP) جاهزة.")
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🔄 تغيير رقم الهاتف", callback_data="change_phone_number"))
                bot.send_message(chat_id, "🔢 **مطلوب كود التفعيل:**\n\nأرسل الكود (4 أرقام) في رسالة عادية الآن...", reply_markup=markup, parse_mode="Markdown")
                
                USER_STATE["waiting_for"] = "otp"
                USER_STATE["input_data"] = None
                USER_STATE["input_event"].clear()
                USER_STATE["change_phone"] = False
                
                if not USER_STATE["input_event"].wait(timeout=180):
                    browser.close()
                    chrome_browser.close()
                    return False, "انتهى وقت الانتظار للكود (3 دقائق)."
                    
                USER_STATE["waiting_for"] = None 
                
                if USER_STATE["change_phone"]:
                    bot.send_message(chat_id, "🔄 جاري العودة لصفحة رقم الهاتف...")
                    try:
                        change_btn = signup_page.locator(':is(button, a):has-text("Change"), :is(button, a):has-text("تغيير")').first
                        change_btn.click()
                        signup_page.wait_for_timeout(4000)
                    except:
                        signup_page.go_back()
                        signup_page.wait_for_timeout(4000)
                    continue 
                    
                otp_code = USER_STATE["input_data"]
                
                bot.send_message(chat_id, f"⏳ جاري إدخال الكود `{otp_code}` وتأكيد الحساب...")
                try:
                    otp_input = signup_page.locator('input[type="text"], input[name="code"], input[name="otp"]').first
                    otp_input.fill(otp_code)
                    signup_page.wait_for_timeout(1000)
                    send_progress_photo(signup_page, chat_id, "📸 [13] تم كتابة الكود وقبل المتابعة.")
                    
                    signup_page.keyboard.press("Enter")
                    signup_page.wait_for_timeout(6000)
                    
                    signup_page.keyboard.press("Enter")
                    signup_page.wait_for_timeout(4000)
                except Exception:
                    signup_page.keyboard.press("Enter")
                    
                send_progress_photo(signup_page, chat_id, "📸 [14] واجهة الحساب النهائية بعد التفعيل والانتهاء.")
                break 
                
            browser.close()
            chrome_browser.close()
            return True, {"links": netflix_links, "text": "تم إنهاء تسجيل الحساب كاملاً وربط الهاتف بنجاح!"}
            
    except Exception as e:
        return False, f"خطأ: {str(e)}"

# --- القوائم السفلية ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    
    if USER_STATE["is_pinned"]:
        btn_screenshot_new = InlineKeyboardButton("📸 فتح صفحة جديدة (منفصلة)", callback_data="take_screenshot")
        btn_screenshot_pinned = InlineKeyboardButton("📌 عرض الصفحة المثبتة", callback_data="view_pinned_page")
        
        btn_auto = InlineKeyboardButton("🚀 إنشاء الحساب وتفعيل الهاتف", callback_data="start_auto")
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

    if call.data == "change_phone_number":
        if USER_STATE["waiting_for"] == "otp":
            USER_STATE["change_phone"] = True
            USER_STATE["input_event"].set() 
            bot.answer_callback_query(call.id, "🔄 جاري العودة لخطوة رقم الهاتف...")
        else:
            bot.answer_callback_query(call.id, "❌ لا يمكن تغيير الرقم الآن.", show_alert=True)
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
                msg = f"✅ **اكتمل إنشاء الحساب بالكامل!**\n\n📧 `{target_email}`\n\n📄 **النتيجة:**\n{result['text']}"
                bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=main_keyboard())
            else:
                bot.send_message(chat_id, f"❌ **توقفت العملية:**\n{result}", reply_markup=main_keyboard(), parse_mode="Markdown")

        threading.Thread(target=run_automation).start()

    elif call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري فتح صفحة جديدة...")
        bot.edit_message_text("⏳ جاري الفتح...", chat_id, call.message.message_id)
        
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

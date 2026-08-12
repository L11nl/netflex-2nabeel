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

# محاولة استدعاء مكتبة التخفي السحرية
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

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
    """دالة لتطبيق التخفي على المتصفح لمنع اكتشافه من نتفلكس وجوجل"""
    if stealth_sync:
        stealth_sync(page)
    else:
        # حقن كود احتياطي لإخفاء بصمة البوت إذا لم يتم تثبيت المكتبة
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def send_progress_photo(page, chat_id, caption):
    try:
        screenshot_bytes = page.screenshot(full_page=False, timeout=15000)
        bot.send_photo(chat_id, screenshot_bytes, caption=caption)
    except Exception:
        pass # تجاهل الخطأ لكي لا نضيع الوقت في حال فشل التقاط الصورة

def take_screenshot_with_proxy(target_url, session_file=None, image_file=None, max_retries=5):
    for attempt in range(1, max_retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                    args=['--disable-blink-features=AutomationControlled', '--disable-infobars']
                )
                
                context_options = {
                    'viewport': {'width': 1280, 'height': 720},
                    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                if session_file and os.path.exists(session_file):
                    context_options['storage_state'] = session_file
                
                context = browser.new_context(**context_options)
                page = context.new_page()
                apply_stealth(page) # تطبيق التخفي هنا
                
                page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                screenshot_bytes = page.screenshot(full_page=False, timeout=20000)
                
                if session_file:
                    context.storage_state(path=session_file)
                if image_file:
                    with open(image_file, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                browser.close()
                return screenshot_bytes, "Success"
        except Exception:
            time.sleep(1)
            
    return None, "فشل الاتصال"

def execute_netflix_automation(session_file, image_file, email, chat_id):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": PROXY_SERVER, "username": PROXY_USERNAME, "password": PROXY_PASSWORD},
                args=['--disable-blink-features=AutomationControlled', '--disable-infobars']
            )
            
            context = browser.new_context(
                storage_state=session_file if os.path.exists(session_file) else None,
                viewport={'width': 1280, 'height': 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            netflix_page = context.new_page()
            apply_stealth(netflix_page) # تطبيق التخفي الجذري هنا
            
            # --- الخطوة 1: فتح الصفحة ---
            bot.send_message(chat_id, "⏳ جاري تنفيذ العملية (المرور المخفي)...")
            netflix_page.goto("https://www.netflix.com/login", timeout=60000, wait_until="domcontentloaded")
            netflix_page.wait_for_timeout(4000)
            
            # --- الخطوة 2: تجاوز reCAPTCHA بأمان ---
            for attempt in range(1, 4):
                try:
                    email_input = netflix_page.locator("input[name='email'], input[name='userLoginId'], input[type='email']").first
                    if email_input.is_visible(timeout=5000):
                        email_input.click()
                        email_input.fill("")
                        email_input.type(email, delay=150)
                        netflix_page.wait_for_timeout(1000)
                except:
                    pass
                
                try:
                    continue_btn = netflix_page.locator(':is(button, a):has-text("Continue"), :is(button, a):has-text("Next"), :is(button, a):has-text("متابعة"), :is(button, a):has-text("التالي")').first
                    if continue_btn.is_visible(timeout=3000):
                        continue_btn.click(timeout=10000)
                    else:
                        email_input.press("Enter")
                except:
                    try: email_input.press("Enter")
                    except: pass
                    
                netflix_page.wait_for_timeout(6000)
                
                try:
                    error_msg = netflix_page.locator('text="Something went wrong"').first
                    if error_msg.is_visible(timeout=3000):
                        context.clear_cookies() # تنظيف كامل للهوية
                        netflix_page.reload(timeout=60000, wait_until="domcontentloaded")
                        netflix_page.wait_for_timeout(4000)
                        continue 
                except:
                    pass
                    
                break 
                
            # --- الخطوة 3: إرسال الرابط سريعاً ---
            for i in range(1, 4):
                try:
                    resend_btn = netflix_page.locator(':is(button, a):has-text("Resend Link"), :is(button, a):has-text("إعادة إرسال")').first
                    if resend_btn.is_visible(timeout=3000):
                        bot.send_message(chat_id, "✅ تم إرسال رسالة نتفلكس بنجاح!")
                        break
                        
                    try:
                        email_input_again = netflix_page.locator("input[name='email'], input[name='userLoginId'], input[type='email']").first
                        if email_input_again.is_visible(timeout=2000) and not email_input_again.input_value():
                            email_input_again.type(email, delay=150)
                            netflix_page.wait_for_timeout(1000)
                    except: pass
                    
                    next_btn = netflix_page.locator(':is(button, a):has-text("Send Link"), :is(button, a):has-text("إرسال الرابط"), :is(button, a):has-text("Next"), :is(button, a):has-text("Continue"), :is(button, a):has-text("التالي"), :is(button, a):has-text("متابعة")').first
                    
                    if next_btn.is_visible(timeout=4000):
                        next_btn.click(timeout=10000)
                        netflix_page.wait_for_timeout(6000)
                    else:
                        break 
                except Exception:
                    break
            
            # --- الخطوة 4: صندوق البريد ---
            email_page = context.new_page()
            apply_stealth(email_page) # تطبيق التخفي على البريد أيضاً
            
            email_page.goto(f"https://generator.email/inbox9/{email}", timeout=60000, wait_until="domcontentloaded")
            email_page.wait_for_timeout(10000) 
            
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
        return False, str(e)

# --- القوائم السفلية والباقي بدون تغيير ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    
    if USER_STATE["is_pinned"]:
        btn_screenshot_new = InlineKeyboardButton("📸 فتح صفحة جديدة (منفصلة)", callback_data="take_screenshot")
        btn_screenshot_pinned = InlineKeyboardButton("📌 عرض الصفحة المثبتة", callback_data="view_pinned_page")
        
        btn_auto = InlineKeyboardButton("🚀 إدخال الإيميل وجلب الروابط", callback_data="start_auto")
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
                bot.send_message(chat_id, f"❌ **خطأ:**\n`{result}`", reply_markup=main_keyboard(), parse_mode="Markdown")

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

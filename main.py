import time
import threading
import os
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- إعدادات البيئة والتوكن ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "643309456"))
SMS_API_KEY = os.environ.get("SMS_API_KEY", "3jdatCdMpWM5NAE5JWJ64T71uEAGRXpW")

BASE_URL = "https://smsbower.page/stubs/handler_api.php"

# إعدادات البروكسي
PROXY_SERVER = "http://gw.dataimpulse.com:823"
PROXY_USERNAME = "a2554925de14dc8880af"
PROXY_PASSWORD = "b48bdda8a174e3aa"

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return user_id == ALLOWED_USER_ID

# --- دالة التقاط الصورة والبحث عن عرض 30 يوم ---
def take_screenshot_with_proxy(target_url, max_retries=15): # تم زيادة المحاولات إلى 15
    last_error = ""
    for attempt in range(1, max_retries + 1):
        print(f"🔄 المحاولة {attempt}: جاري البحث عن عرض (Try 30 Days for USD 0)...")
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
                
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                page = context.new_page()
                
                page.goto(target_url, timeout=20000, wait_until="load")
                page.wait_for_timeout(3000)
                
                # جلب كل النصوص الموجودة في الصفحة للبحث فيها
                page_content = page.content()
                
                # التحقق من وجود النص المطلوب
                if "Try 30 Days for USD 0" in page_content:
                    print(f"✅ تم العثور على العرض في المحاولة {attempt}!")
                    screenshot_bytes = page.screenshot(full_page=True)
                    browser.close()
                    return screenshot_bytes, "Success"
                else:
                    # في حال لم يجد النص، نغلق المتصفح ونقوم بتوليد خطأ متعمد للذهاب للمحاولة التالية (IP جديد)
                    browser.close()
                    raise Exception("الصفحة فتحت لكن لا يوجد عرض (Try 30 Days for USD 0) في هذا الـ IP.")
                
        except PlaywrightTimeoutError as e:
            last_error = "تأخر الرد لأكثر من 20 ثانية (Timeout)."
            print(f"⚠️ {last_error} - جاري تبديل الـ IP...")
            time.sleep(1)
        except Exception as e:
            last_error = str(e)
            print(f"❌ {last_error}")
            time.sleep(1)
            
    return None, "تم استنفاد جميع المحاولات ولم يتم العثور على العرض المذكور."

# --- لوحة المفاتيح الرئيسية ---
def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    btn_screenshot = InlineKeyboardButton("📸 صيد عرض 30 يوم مجاني", callback_data="take_screenshot")
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

    if call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري البحث عن العرض...")
        bot.edit_message_text(
            "⏳ جارٍ العمل... يتم الآن تدوير البروكسيات للبحث عن عرض `Try 30 Days for USD 0` (قد يستغرق الأمر بعض الوقت)...",
            chat_id, 
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        def process_screenshot():
            url = "https://www.netflix.com/clearcookies"
            photo_bytes, error_msg = take_screenshot_with_proxy(url)
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(chat_id, photo_bytes, caption="✅ تم اصطياد العرض بنجاح!")
                bot.send_message(chat_id, "القائمة الرئيسية:", reply_markup=main_keyboard())
            else:
                bot.edit_message_text(
                    f"❌ لم يتم العثور على العرض.\n\n*السبب:*\n`{error_msg}`",
                    chat_id, 
                    call.message.message_id,
                    reply_markup=main_keyboard(),
                    parse_mode="Markdown"
                )
                
        threading.Thread(target=process_screenshot).start()

    elif call.data == "change_netflix_pass":
        bot.answer_callback_query(call.id, "جاري تحضير الأتمتة...")
        bot.edit_message_text("⏳ جارٍ العمل...", chat_id, call.message.message_id)

    elif call.data == "toggle_logout":
        bot.answer_callback_query(call.id, "تم تغيير حالة تسجيل الخروج", show_alert=False)

print("البوت يعمل الآن...")
bot.infinity_polling()

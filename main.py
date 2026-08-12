import time
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from playwright.sync_api import sync_playwright

# --- إعدادات البيئة والتوكن (يفضل وضعها في Railway Environment Variables) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا_أو_في_ريلوي")
BASE_URL = "https://smsbower.page/stubs/handler_api.php"

# إعداد البروكسي الخاص بك
PROXY_SERVER = "http://a2554925de14dc8880af:b48bdda8a174e3aa@gw.dataimpulse.com:823"

bot = telebot.TeleBot(BOT_TOKEN)

# --- بيانات المستخدمين المسموح لهم ---
USERS = {
    643309456: {
        "name": "نبيل",
        "3jdatCdMpWM5NAE5JWJ64T71uEAGRXpW": "الايباي مال موقع الارقام"
    }
}

user_states = {}

def get_user_data(user_id):
    return USERS.get(user_id, None)

# --- دالة التقاط الصورة باستخدام Playwright مع البروكسي ---
def take_screenshot_with_proxy(target_url):
    try:
        with sync_playwright() as p:
            # تشغيل المتصفح المخفي وربطه بالبروكسي
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": PROXY_SERVER}
            )
            page = browser.new_page()
            
            # الذهاب إلى الرابط
            page.goto(target_url, timeout=60000)
            
            # التقاط صورة للشاشة
            screenshot_bytes = page.screenshot(full_page=True)
            browser.close()
            return screenshot_bytes
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

# --- لوحة المفاتيح الرئيسية ---
def main_keyboard(user_id):
    user = get_user_data(user_id)
    if not user:
        return None
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    
    # الأزرار الجديدة
    btn_change_netflix = InlineKeyboardButton("🔄 تغيير رمز النتفلكس", callback_data="change_netflix_pass")
    btn_toggle_logout = InlineKeyboardButton("📱 تسجيل الخروج من جميع الأجهزة: [مفعل ✅]", callback_data="toggle_logout")
    btn_screenshot = InlineKeyboardButton("📸 الدخول إلى الرابط (Clear Cookies)", callback_data="take_screenshot")
    
    markup.add(btn_change_netflix, btn_toggle_logout, btn_screenshot)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        bot.send_message(message.chat.id, "عذراً، هذا البوت مخصص لأشخاص محددين فقط ❌")
        return

    bot.send_message(
        message.chat.id,
        f"مرحباً بك يا **{user['name']}** في لوحة تحكم الإدارة ⚙️\n\nاختر الإجراء الذي تريده من القائمة أدناه:",
        reply_markup=main_keyboard(user_id),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if not get_user_data(user_id):
        bot.answer_callback_query(call.id, "هذا البوت ليس مخصصاً لك!", show_alert=True)
        return

    # --- زر الدخول للرابط والتقاط الصورة ---
    if call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري المعالجة...")
        bot.edit_message_text(
            "⏳ جارٍ العمل... جاري الاتصال بالبروكسي العراقي 🇮🇶 وفتح الرابط...",
            chat_id, 
            call.message.message_id
        )
        
        # تشغيل الدالة في مسار منفصل (Thread) كي لا يتوقف البوت
        def process_screenshot():
            url = "http://netflix.com/clearcookies"
            photo_bytes = take_screenshot_with_proxy(url)
            
            if photo_bytes:
                bot.delete_message(chat_id, call.message.message_id)
                bot.send_photo(chat_id, photo_bytes, caption="✅ تم الدخول إلى الرابط بنجاح.")
                bot.send_message(chat_id, "القائمة الرئيسية:", reply_markup=main_keyboard(user_id))
            else:
                bot.edit_message_text(
                    "❌ حدث خطأ أثناء محاولة فتح الرابط عبر البروكسي.",
                    chat_id, 
                    call.message.message_id,
                    reply_markup=main_keyboard(user_id)
                )
                
        threading.Thread(target=process_screenshot).start()

    # --- الأزرار الأخرى (هيكل فقط كما طلبت للعمل الصامت) ---
    elif call.data == "change_netflix_pass":
        bot.answer_callback_query(call.id, "جاري تحضير الأتمتة...")
        bot.edit_message_text(
            "⏳ جارٍ العمل...",
            chat_id, 
            call.message.message_id
        )
        # هنا يتم وضع كود تغيير الرمز بالمتصفح المخفي
        # ...
        # عند الانتهاء:
        # bot.edit_message_text("تم تغيير كلمة المرور بنجاح ✅", chat_id, call.message.message_id, reply_markup=main_keyboard(user_id))

    elif call.data == "toggle_logout":
        # هذه ميزة شكلية حالياً للتبديل، يمكنك برمجتها لتغيير حالة متغير
        bot.answer_callback_query(call.id, "تم تغيير حالة تسجيل الخروج", show_alert=False)

print("البوت يعمل الآن...")
bot.infinity_polling()

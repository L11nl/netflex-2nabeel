import threading
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from playwright.sync_api import sync_playwright

# --- إعدادات ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_هنا")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "643309456"))

bot = telebot.TeleBot(BOT_TOKEN)

# --- إدارة الجلسات في الذاكرة ---
# active_sessions[chat_id] = {'context': ctx, 'page': page, 'is_pinned': bool}
active_sessions = {}

# تهيئة المتصفح مرة واحدة عند تشغيل البوت
p = sync_playwright().start()
browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])

def get_session(chat_id):
    if chat_id not in active_sessions:
        ctx = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()
        active_sessions[chat_id] = {'context': ctx, 'page': page, 'is_pinned': False}
    return active_sessions[chat_id]

def close_session(chat_id):
    if chat_id in active_sessions:
        active_sessions[chat_id]['context'].close()
        del active_sessions[chat_id]

# --- الكود الرئيسي ---

def main_keyboard(chat_id):
    markup = InlineKeyboardMarkup()
    session = active_sessions.get(chat_id)
    
    is_pinned = session and session.get('is_pinned', False)
    
    markup.add(InlineKeyboardButton("📸 الدخول/تحديث الصفحة", callback_data="take_screenshot"))
    
    if is_pinned:
        markup.add(InlineKeyboardButton("❌ إلغاء تثبيت الجلسة (إغلاق)", callback_data="unpin_session"))
    else:
        markup.add(InlineKeyboardButton("📌 تثبيت الجلسة (عزل)", callback_data="pin_session"))
        
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data == "take_screenshot":
        bot.answer_callback_query(call.id, "جاري المعالجة...")
        session = get_session(chat_id)
        page = session['page']
        
        try:
            page.goto("https://www.netflix.com/clearcookies", timeout=20000)
            page.wait_for_timeout(2000)
            screenshot = page.screenshot(full_page=True)
            bot.send_photo(chat_id, screenshot, caption="✅ تم الوصول للصفحة.", reply_markup=main_keyboard(chat_id))
        except Exception as e:
            bot.send_message(chat_id, f"❌ خطأ: {e}")

    elif call.data == "pin_session":
        session = get_session(chat_id)
        session['is_pinned'] = True
        bot.answer_callback_query(call.id, "تم تثبيت الجلسة! ستبقى مفتوحة.")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=main_keyboard(chat_id))

    elif call.data == "unpin_session":
        close_session(chat_id)
        bot.answer_callback_query(call.id, "تم إلغاء التثبيت وإغلاق الجلسة.")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=main_keyboard(chat_id))

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "لوحة التحكم:", reply_markup=main_keyboard(message.chat.id))

bot.infinity_polling()

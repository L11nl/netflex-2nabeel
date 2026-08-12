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
    "change_phone": False,
    "cancel_flow": False
}

# 🔹 الكوكيز الثابتة لتجميد عرض 30 يوم 🔹
RAW_COOKIES = [
  {"name": "flwssn", "value": "b2cdd378-f151-4ae8-bc62-a3f304f10265", "domain": ".netflix.com", "path": "/", "expires": 1786557170.196962, "httpOnly": False, "secure": False, "sameSite": "unspecified"},
  {"name": "gsid", "value": "31793dad-378b-4b3f-a31d-6830273a78f5", "domain": ".netflix.com", "path": "/", "expires": 1786632766.470792, "httpOnly": True, "secure": True, "sameSite": "no_restriction"},
  {"name": "netflix-sans-bold-3-loaded", "value": "true", "domain": ".netflix.com", "path": "/", "expires": 1794322370.19694, "httpOnly": False, "secure": False, "sameSite": "unspecified"},
  {"name": "netflix-sans-normal-3-loaded", "value": "true", "domain": ".netflix.com", "path": "/", "expires": 1794322370.196915, "httpOnly": False, "secure": False, "sameSite": "unspecified"},
  {"name": "NetflixId", "value": "v%3D3%26ct%3DBgjHlOvcAxKrAsPHtSnrZ9GKORSMuemrTl8covHfrSmMHg1VM44L77Jrwx2uMz07p6sVGf_wgQ347NiE9t-E6u6b1UIjzpLBZj3RK-K12h2a9fOSlqkzKuknBnpr9jq_r_CA258gC-GIMbcVrrpesjVwF_PFBsXdBEvXRpBITMlUtc9t8ZYnmXJhc-UYji_EIctXdNnTV58Q5z2C4uu0_UeYZdSjHfJ7kaWwoiTq4gXly5kgGIL3lYyLGIuI64ektCOwtw56c3xeAxi347qIWa9yUJu98ag5MFObpYDnt7dtyb_t1sWrLejZLVFlmRH3O1tvrGNQ1Gg1YWtu8M2UyONPETTUIk03-XuwOeq38x38W5yhRkQERjLBXMxxfEE2riISV__maFrywZ0aM2XKOy121xIUGAYiDgoMWP4bq858s_MFPNW8", "domain": ".netflix.com", "path": "/", "expires": 1818082366.470752, "httpOnly": False, "secure": True, "sameSite": "lax"},
  {"name": "nfvdid", "value": "BQFmAAEBEFG3E8P1gRYF0CWTHucUHvRAr4WoXZoXMCJsHpmZWCwV23Wvz4jL7B_S3wcmhclGbFwicS-7sV38gw0R4uqceBim1JQ-_tiQJZ0wUNES6bl9Yw%3D%3D", "domain": ".netflix.com", "path": "/", "expires": 1817250051.048752, "httpOnly": False, "secure": False, "sameSite": "unspecified"},
  {"name": "nkufi-bold-4-loaded", "value": "true", "domain": ".netflix.com", "path": "/", "expires": 1794322370.19689, "httpOnly": False, "secure": False, "sameSite": "unspecified"},
  {"name": "nkufi-normal-4-loaded", "value": "true", "domain": ".netflix.com", "path": "/", "expires": 1794322370.196801, "httpOnly": False, "secure": False, "sameSite": "unspecified"},
  {"name": "OptanonConsent", "value": "isGpcEnabled=0&datestamp=Wed+Aug+12+2026+17%3A52%3A50+GMT%2B0300+(%D8%A7%D9%84%D8%AA%D9%88%D9%82%D9%8A%D8%AA+%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A+%D8%A7%D9%84%D8%B1%D8%B3%D9%85%D9%8A)&version=202604.2.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&hosts=&consentId=64d3de31-d011-461b-9a7e-f01a992fcfb5&interactionCount=1&isAnonUser=1&prevHadToken=0&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&crTime=1785714057627&AwaitingReconsent=false", "domain": ".netflix.com", "path": "/", "expires": 1818082370, "httpOnly": False, "secure": False, "sameSite": "lax"},
  {"name": "OTSessionTracking", "value": "87b6a5c0-0104-4e96-a291-092c11350111", "domain": "www.netflix.com", "path": "/", "expires": 1786632769, "httpOnly": False, "secure": False, "sameSite": "lax"},
  {"name": "SecureNetflixId", "value": "v%3D3%26mac%3DAQEAEQABABQrKG3XWM4a01dvho67JcWEdpgOEh3Iqnw.%26dt%3D1786546366150", "domain": ".netflix.com", "path": "/", "expires": 1818082366.470711, "httpOnly": False, "secure": True, "sameSite": "strict"}
]

def sanitize_cookies(cookies):
    clean = []
    for c in cookies:
        nc = {"name": c["name"], "value": c["value"], "domain": c["domain"], "path": c["path"]}
        if "expires" in c: nc["expires"] = float(c["expires"])
        if "httpOnly" in c: nc["httpOnly"] = c["httpOnly"]
        if "secure" in c: nc["secure"] = c["secure"]
        if "sameSite" in c:
            ss = c["sameSite"].lower()
            if ss in ["lax", "strict", "none"]: nc["sameSite"] = ss.capitalize()
            elif ss == "no_restriction": nc["sameSite"] = "None"
        clean.append(nc)
    return clean

def generate_random_email(length):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{username}@5xu.vn"

def apply_stealth(page):
    if stealth_sync:
        stealth_sync(page)
    else:
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def safely_goto(page, url, timeout=45000):
    try:
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    except Exception:
        pass 
    page.wait_for_timeout(4000)

def send_progress_photo(page, chat_id, caption):
    try:
        page.wait_for_timeout(2000) 
        screenshot_bytes = page.screenshot(full_page=False, timeout=20000)
        bot.send_photo(chat_id, screenshot_bytes, caption=caption)
    except Exception as e:
        bot.send_message(chat_id, f"{caption}\n\n*(⚠️ تعذر التقاط الصورة لكن العملية مستمرة...)*", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: USER_STATE["waiting_for"] in ["phone", "otp"])
def handle_interactive_input(message):
    if not is_admin(message.from_user.id):
        return
    USER_STATE["input_data"] = message.text.strip()
    USER_STATE["input_event"].set()
    bot.send_message(message.chat.id, "✅ تم استلام الإدخال، جاري تطبيقه في المتصفح الآن...")

# --- دالة فتح الصفحة المنفصلة (الآن تخبرك بأي محاولة وتقوم بحقن الكوكيز) ---
def take_screenshot_with_proxy(target_url, chat_id=None, msg_id=None, session_file=None, image_file=None, max_retries=3):
    for attempt in range(1, max_retries + 1):
        if chat_id and msg_id:
            try:
                bot.edit_message_text(f"⏳ جاري الفتح... (المحاولة {attempt} من {max_retries})\nيرجى الانتظار...", chat_id, msg_id)
            except: pass
            
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
                
                # 🔥 حقن الكوكيز السحرية لمنع A/B Testing حتى في الصفحة المثبتة 🔥
                context.add_cookies(sanitize_cookies(RAW_COOKIES))
                
                page = context.new_page()
                apply_stealth(page) 
                
                safely_goto(page, target_url, timeout=45000)
                screenshot_bytes = page.screenshot(full_page=False, timeout=20000)
                
                if session_file: context.storage_state(path=session_file)
                if image_file:
                    with open(image_file, 'wb') as f: f.write(screenshot_bytes)
                browser.close()
                return screenshot_bytes, "Success"
        except Exception as e:
            time.sleep(2)
            
    return None, "فشل الاتصال بالبروكسي. يرجى المحاولة لاحقاً."

# --- دالة الأتمتة الشاملة ---
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
            context.add_cookies(sanitize_cookies(RAW_COOKIES))
            
            netflix_page = context.new_page()
            apply_stealth(netflix_page)
            
            # --- المرحلة 1: التسجيل المبدئي ---
            bot.send_message(chat_id, "⏳ جاري فتح صفحة نتفلكس بالكوكيز الجديدة...")
            safely_goto(netflix_page, "https://www.netflix.com/login")
            send_progress_photo(netflix_page, chat_id, "📸 [1] تم فتح صفحة نتفلكس الرئيسية.")
            
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
                continue_btn = netflix_page.locator(':is(button, a):has-text("Continue"), :is(button, a):has-text("Next"), :is(button, a):has-text("متابعة"), :is(button, a):has-text("التالي"), button[type="submit"]').first
                if continue_btn.is_visible(timeout=3000):
                    continue_btn.hover()
                    netflix_page.wait_for_timeout(500)
                    continue_btn.click(force=True, timeout=10000)
                else:
                    email_input.press("Enter")
            except:
                try: email_input.press("Enter")
                except: pass
                
            netflix_page.wait_for_timeout(1000)
            try: netflix_page.keyboard.press("Enter")
            except: pass
            
            netflix_page.wait_for_timeout(7000)
            send_progress_photo(netflix_page, chat_id, "📸 [2] الصفحة بعد إدخال الإيميل والمحاولة.")
            
            try:
                error_msg = netflix_page.locator('text="Something went wrong"').first
                if error_msg.is_visible(timeout=3000):
                    send_progress_photo(netflix_page, chat_id, "📸 [تحذير] ظهر الخطأ الأحمر، جاري التحديث...")
                    netflix_page.reload(timeout=60000, wait_until="domcontentloaded")
                    netflix_page.wait_for_timeout(5000)
            except:
                pass
                
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
            
            # --- صندوق البريد ---
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

            bot.send_message(chat_id, f"🔗 تم إيجاد رابط إكمال التسجيل!\n`{epr_link}`\n\n⏳ جاري فتح الرابط بانتظار للتحميل...")
            
            # -------------------------------------------------------------
            # 🔥 المرحلة الثانية: فتح رابط epr وإكمال التسجيل 🔥
            # -------------------------------------------------------------
            signup_page = context.new_page()
            apply_stealth(signup_page)
            
            safely_goto(signup_page, epr_link, timeout=60000)
            signup_page.wait_for_timeout(6000) 

            # الانتظار الذكي لزر Finish لمنع الشاشة البيضاء
            finish_btn = signup_page.locator(':is(button, a):has-text("Finish"), :is(button, a):has-text("إكمال")').first
            try:
                finish_btn.wait_for(state="visible", timeout=20000)
                send_progress_photo(signup_page, chat_id, "📸 [5] تم تحميل رابط إكمال التسجيل بنجاح (ظهر الزر).")
                
                finish_btn.click(force=True, timeout=10000)
                signup_page.wait_for_timeout(6000)
                send_progress_photo(signup_page, chat_id, "📸 [6] تم الضغط على زر (Finish Sign-Up) بنجاح.")
            except Exception as e:
                send_progress_photo(signup_page, chat_id, "📸 [5-تحذير] تعذر إيجاد زر Finish أو الصفحة بيضاء، سنحاول المتابعة...")
                signup_page.keyboard.press("Enter")
                signup_page.wait_for_timeout(5000)

            for i in range(1, 4):
                try:
                    next_btn_extra = signup_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي"), :is(button, a):has-text("Continue")').first
                    if next_btn_extra.is_visible(timeout=4000):
                        next_btn_extra.click(force=True)
                        signup_page.wait_for_timeout(5000)
                        send_progress_photo(signup_page, chat_id, f"📸 [تخطي] تم الضغط على التالي ({i}).")
                    else:
                        break
                except:
                    break

            send_progress_photo(signup_page, chat_id, "📸 [7] الشاشة الحالية قبل اختيار فاتورة الهاتف.")

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
                
                markup_phone = InlineKeyboardMarkup()
                markup_phone.add(InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_operation"))
                bot.send_message(chat_id, "📱 **مطلوب رقم الهاتف:**\n\nأرسل رقم الهاتف الآن في رسالة عادية (البوت سينتظرك لمدة 3 دقائق)...", reply_markup=markup_phone, parse_mode="Markdown")
                
                USER_STATE["waiting_for"] = "phone"
                USER_STATE["input_data"] = None
                USER_STATE["input_event"].clear()
                USER_STATE["change_phone"] = False
                USER_STATE["cancel_flow"] = False
                
                if not USER_STATE["input_event"].wait(timeout=180) or USER_STATE["cancel_flow"]:
                    browser.close()
                    chrome_browser.close()
                    return False, "تم إلغاء العملية أو انتهى وقت الانتظار."
                    
                phone_num = USER_STATE["input_data"]
                USER_STATE["waiting_for"] = None 
                
                bot.send_message(chat_id, f"⏳ جاري إدخال الرقم `{phone_num}` والموافقة على الشروط...")
                try:
                    phone_input = signup_page.locator('input[type="tel"], input[name="phoneNumber"]').first
                    phone_input.fill(phone_num)
                    signup_page.wait_for_timeout(1000)
                    
                    try:
                        signup_page.locator('text="I agree"').click(force=True)
                    except:
                        signup_page.locator('input[type="checkbox"]').last.check(force=True)
                    signup_page.wait_for_timeout(1000)
                    
                    send_progress_photo(signup_page, chat_id, "📸 [11] تم إدخال الرقم وتحديد مربع (I agree).")
                    
                    verify_btn = signup_page.locator(':is(button, a):has-text("Verify Phone Number"), :is(button, a):has-text("التحقق")').first
                    verify_btn.click(timeout=10000)
                    signup_page.wait_for_timeout(6000)
                except Exception as e:
                    pass

                send_progress_photo(signup_page, chat_id, "📸 [12] صفحة إدخال الكود (OTP) جاهزة.")
                
                markup_otp = InlineKeyboardMarkup()
                markup_otp.row(InlineKeyboardButton("🔄 تغيير رقم الهاتف", callback_data="change_phone_number"))
                markup_otp.row(InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_operation"))
                bot.send_message(chat_id, "🔢 **مطلوب كود التفعيل:**\n\nأرسل الكود (4 أرقام) في رسالة عادية الآن...", reply_markup=markup_otp, parse_mode="Markdown")
                
                USER_STATE["waiting_for"] = "otp"
                USER_STATE["input_data"] = None
                USER_STATE["input_event"].clear()
                USER_STATE["change_phone"] = False
                USER_STATE["cancel_flow"] = False
                
                if not USER_STATE["input_event"].wait(timeout=180) or USER_STATE["cancel_flow"]:
                    browser.close()
                    chrome_browser.close()
                    return False, "تم إلغاء العملية بناءً على طلبك."
                    
                USER_STATE["waiting_for"] = None 
                
                if USER_STATE["change_phone"]:
                    bot.send_message(chat_id, "🔄 جاري العودة لصفحة رقم الهاتف وتحديثها...")
                    try:
                        change_btn = signup_page.locator(':is(button, a):has-text("Change"), :is(button, a):has-text("تغيير")').first
                        if change_btn.is_visible(timeout=3000):
                            change_btn.click()
                        else:
                            signup_page.go_back()
                    except:
                        signup_page.go_back()
                        
                    signup_page.wait_for_timeout(3000)
                    try:
                        signup_page.reload(timeout=40000, wait_until="domcontentloaded")
                    except:
                        pass
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

    # معالجة زر إلغاء العملية
    if call.data == "cancel_operation":
        if USER_STATE["waiting_for"] in ["phone", "otp"]:
            USER_STATE["cancel_flow"] = True
            USER_STATE["input_event"].set()
            bot.answer_callback_query(call.id, "❌ تم إلغاء العملية بنجاح.")
        else:
            bot.answer_callback_query(call.id, "❌ لا توجد عملية تفاعلية لإلغائها حالياً.", show_alert=True)
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
        
        def process_screenshot():
            try:
                url = "https://www.netflix.com/clearcookies"
                for file_name in [USER_STATE["temp_session"], USER_STATE["temp_image"]]:
                    if os.path.exists(file_name): os.remove(file_name)
                    
                photo_bytes, error_msg = take_screenshot_with_proxy(
                    target_url=url, 
                    chat_id=chat_id, 
                    msg_id=call.message.message_id,
                    session_file=USER_STATE["temp_session"], 
                    image_file=USER_STATE["temp_image"]
                )
                
                if photo_bytes:
                    bot.delete_message(chat_id, call.message.message_id)
                    bot.send_photo(chat_id, photo_bytes, caption="✅ هل تريد التثبيت؟", reply_markup=photo_keyboard(is_viewing_pinned=False))
                else:
                    bot.edit_message_text(f"❌ فشل:\n`{error_msg}`", chat_id, call.message.message_id, reply_markup=main_keyboard(), parse_mode="Markdown")
            except Exception as e:
                bot.edit_message_text(f"❌ حدث خطأ غير متوقع أثناء الفتح:\n`{str(e)}`", chat_id, call.message.message_id, reply_markup=main_keyboard())
                
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

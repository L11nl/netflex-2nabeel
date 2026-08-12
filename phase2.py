# -*- coding: utf-8 -*-
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def complete_signup_phase(ctx):
    # استخراج المتغيرات من الحزمة
    context = ctx["context"]
    browser = ctx["browser"]
    chrome_browser = ctx["chrome_browser"]
    epr_link = ctx["epr_link"]
    chat_id = ctx["chat_id"]
    bot = ctx["bot"]
    USER_STATE = ctx["USER_STATE"]
    apply_stealth = ctx["apply_stealth"]
    safely_goto = ctx["safely_goto"]
    send_progress_photo = ctx["send_progress_photo"]
    netflix_links = ctx["netflix_links"]

    # -------------------------------------------------------------
    # 🔥 المرحلة الثانية: التنقل الذكي للوصول إلى طرق الدفع 🔥
    # -------------------------------------------------------------
    signup_page = context.new_page()
    apply_stealth(signup_page)
    safely_goto(signup_page, epr_link)
    
    send_progress_photo(signup_page, chat_id, "📸 [5] تم فتح رابط إكمال التسجيل (EPR).")
    bot.send_message(chat_id, "⏳ جاري فحص صفحات العروض وتخطيها للوصول لصفحة الدفع...")

    payment_page_reached = False
    
    # حلقة ذكية للبحث عن زر "فاتورة الهاتف" وتخطي أي صفحات تعترض الطريق (تعمل 5 مرات كحد أقصى)
    for step in range(1, 6):
        signup_page.wait_for_timeout(4000) # انتظار استقرار الصفحة لتجنب الأخطاء
        
        # 1. فحص هل وصلنا للهدف (خيار فاتورة الهاتف)؟
        mobile_bill_option = signup_page.locator('*:has-text("Add to mobile bill"), *:has-text("فاتورة الهاتف"), *:has-text("فاتورة الجوال")').last
        if mobile_bill_option.is_visible(timeout=3000):
            payment_page_reached = True
            send_progress_photo(signup_page, chat_id, "✅ ممتاز! تم الوصول بنجاح إلى صفحة طرق الدفع.")
            break
            
        # 2. إذا لم نصل، نبحث عن زر "التالي" أو "متابعة" لتخطي الصفحة الحالية
        try:
            # النزول لأسفل الصفحة (لأن زر Next في صفحة الخطط يكون في الأسفل)
            signup_page.keyboard.press("End")
            signup_page.wait_for_timeout(1500)
            
            next_btn = signup_page.locator(':is(button, a):has-text("Finish Sign-Up"), :is(button, a):has-text("Next"), :is(button, a):has-text("Continue"), :is(button, a):has-text("متابعة"), :is(button, a):has-text("التالي")').first
            
            if next_btn.is_visible(timeout=3000):
                send_progress_photo(signup_page, chat_id, f"📸 [تخطي الذكاء الاصطناعي] تم رصد صفحة عرض ({step}). جاري الضغط على التالي...")
                next_btn.click(timeout=10000)
                # ننتظر تحميل الصفحة الجديدة بعد الضغط
                signup_page.wait_for_load_state("domcontentloaded", timeout=15000)
            else:
                signup_page.keyboard.press("Enter")
        except Exception as e:
            pass

    # إذا انتهت المحاولات ولم يصل لخيار الدفع
    if not payment_page_reached:
        bot.send_message(chat_id, "❌ توقفت العملية: نتفلكس لم يظهر صفحة الدفع بعد كل المحاولات.")
        send_progress_photo(signup_page, chat_id, "📸 الشاشة العالقة النهائية:")
        browser.close()
        chrome_browser.close()
        return False, "فشل الوصول لصفحة الدفع."

    # -------------------------------------------------------------
    # 3. اختيار فاتورة الهاتف والعبور لصفحة الرقم
    # -------------------------------------------------------------
    bot.send_message(chat_id, "⏳ جاري اختيار (إضافة إلى فاتورة الهاتف المحمول)...")
    try:
        mobile_bill_option.click(timeout=10000)
        signup_page.wait_for_timeout(2000)
        send_progress_photo(signup_page, chat_id, "📸 [8] تم تحديد خيار (فاتورة الهاتف).")
        
        # الضغط على زر المتابعة بعد اختيار طريقة الدفع
        next_btn2 = signup_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي")').first
        if next_btn2.is_visible(timeout=3000):
            next_btn2.click()
            bot.send_message(chat_id, "⏳ ننتظر تحميل صفحة رقم الهاتف...")
            # الانتظار حتى يتغير الرابط وتحمل الصفحة
            signup_page.wait_for_load_state("domcontentloaded", timeout=20000)
    except Exception:
        signup_page.keyboard.press("Enter")
        signup_page.wait_for_timeout(4000)

    # -------------------------------------------------------------
    # 4. خطوة إدخال رقم الهاتف وكود الـ OTP بذكاء
    # -------------------------------------------------------------
    while True:
        phone_input = signup_page.locator('input[type="tel"], input[name="phoneNumber"]').first
        
        try:
            # الذكاء 1: لن يطلب الرقم إلا إذا كان الحقل موجوداً فعلاً
            phone_input.wait_for(state="visible", timeout=30000)
            send_progress_photo(signup_page, chat_id, "📸 [10] صفحة إدخال رقم الهاتف جاهزة فعلياً أمامنا.")
        except Exception:
            bot.send_message(chat_id, "❌ لم تظهر صفحة إدخال رقم الهاتف! يبدو أن هنالك مشكلة في الخطوات السابقة.")
            send_progress_photo(signup_page, chat_id, "📸 الشاشة الحالية للخطأ:")
            return False, "فشل الوصول لصفحة رقم الهاتف."
        
        bot.send_message(chat_id, "📱 **مطلوب رقم الهاتف العراقي:**\n\nأرسل رقم الهاتف الآن (البوت لن يقبل سوى أرقام عراقية صحيحة)...", parse_mode="Markdown")
        
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
        
        try:
            phone_input.fill(phone_num)
            signup_page.wait_for_timeout(1000)
            
            agree_checkbox = signup_page.locator('input[type="checkbox"]').first
            if agree_checkbox.is_visible():
                agree_checkbox.check(force=True)
                signup_page.wait_for_timeout(1000)
            
            send_progress_photo(signup_page, chat_id, "📸 [11] تم إدخال الرقم بنجاح والضغط على الموافقة.")
            
            verify_btn = signup_page.locator(':is(button, a):has-text("Verify Phone Number"), :is(button, a):has-text("التحقق")').first
            verify_btn.click(timeout=10000)
            
            bot.send_message(chat_id, "⏳ جاري إرسال الرقم وانتظار تحميل صفحة الكود (OTP)...")
            
            # الذكاء 2: لن ينتقل لخطوة الكود أبداً إلا إذا ظهر حقل الكود!
            otp_input = signup_page.locator('input[type="text"], input[name="code"], input[name="otp"]').first
            otp_input.wait_for(state="visible", timeout=30000) 
            
        except Exception as e:
            bot.send_message(chat_id, "⚠️ الرقم غير مدعوم أو أن الصفحة رفضت الانتقال لخطوة الكود.")
            send_progress_photo(signup_page, chat_id, "📸 [الخطأ] الشاشة الحالية:")
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔄 المحاولة برقم آخر", callback_data="change_phone_number"))
            bot.send_message(chat_id, "هل تريد المحاولة برقم آخر؟", reply_markup=markup)
            
            USER_STATE["waiting_for"] = "otp"
            USER_STATE["input_event"].clear()
            USER_STATE["input_event"].wait(timeout=120)
            continue 
            
        send_progress_photo(signup_page, chat_id, "📸 [12] صفحة إدخال الكود (OTP) جاهزة وتم التحقق منها بنجاح.")
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 تغيير رقم الهاتف", callback_data="change_phone_number"))
        bot.send_message(chat_id, "🔢 **مطلوب كود التفعيل:**\n\nأرسل الكود (أرقام فقط) الآن...", reply_markup=markup, parse_mode="Markdown")
        
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
                signup_page.wait_for_load_state("domcontentloaded", timeout=15000)
            except:
                signup_page.go_back()
                signup_page.wait_for_timeout(4000)
            continue 
            
        otp_code = USER_STATE["input_data"]
        
        bot.send_message(chat_id, f"⏳ جاري إدخال الكود `{otp_code}` وتأكيد الحساب...")
        try:
            otp_input.fill(otp_code)
            signup_page.wait_for_timeout(1000)
            send_progress_photo(signup_page, chat_id, "📸 [13] تم كتابة الكود.")
            
            signup_page.keyboard.press("Enter")
            bot.send_message(chat_id, "⏳ ننتظر التحقق النهائي وإنشاء الحساب...")
            signup_page.wait_for_timeout(10000)
            
        except Exception:
            signup_page.keyboard.press("Enter")
            signup_page.wait_for_timeout(10000)
            
        send_progress_photo(signup_page, chat_id, "📸 [14] واجهة الحساب النهائية بعد التفعيل والانتهاء.")
        break 
        
    browser.close()
    chrome_browser.close()
    return True, {"links": netflix_links, "text": "تم إنهاء تسجيل الحساب كاملاً وربط الهاتف بنجاح!"}

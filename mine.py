from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CommandHandler
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import json
import os
from datetime import datetime
import tempfile
import concurrent.futures
import threading
from functools import partial

# ====== إعداد التسجيل ======
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====== بيانات البوت والإعدادات ======
BOT_TOKEN = "8455353751:AAEx9Jla7H_BNPlkDvBPQQBeXdWI8LL9Fi0"
MAX_CONCURRENT_TASKS = 10  # تم تقليل القيمة من 100 إلى 10
SESSION_TIMEOUT = 30 * 60  # 30 دقيقة من عدم النشاط

# إنشاء thread pool للعمليات المتزامنة
executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)

# حالات المحادثة
USERNAME, PASSWORD = range(2)

# تخزين البيانات المؤقتة لكل مستخدم
users_data = {}  # سيكون بهيئة {user_id: BotManager}
active_sessions = {}
session_lock = threading.Lock()

# ====== قاموس الترجمة ======
translation_dict = {
    # أسماء عربية شائعة
    "mohammed": "محمد",
    "ahmed": "أحمد",
    "ali": "علي",
    "hassan": "حسن",
    "hussein": "حسين",
    "omar": "عمر",
    "khaled": "خالد",
    "mustafa": "مصطفى",
    "ibrahim": "إبراهيم",
    "youssef": "يوسف",
    "abdullah": "عبدالله",
    "abdul": "عبد",
    "rahman": "رحمن",
    "raheem": "رحيم",
    "saeed": "سعيد",
    "tariq": "طارق",
    "noor": "نور",
    "jamal": "جمال",
    "faris": "فارس",
    "karim": "كريم",
    "atta": "عطا",
    "güne": "جون",
    "muslim": "مسلم",
    "aqeel": "عقيل",
    "baqir": "باقر",
    "maitham": "ميثم",
    "qussay": "قصي",
    "saad": "سعد",
    "nasser": "ناصر",
    "muamal": "مؤمل",
    "asaad": "أسعد",
    "muntathar": "منتظر",
    "muntader": "منتظر",
    "hataf": "هاتف",
    "jaffar": "جعفر",
    "razzaq": "رزاق",
    "sajjad": "سجاد",
    "qassim": "قاسم",
    "abbas": "عباس",
    "hashim": "هاشم",
    "falah": "فلاح",
    "murtadha": "مرتضى",
    "haider": "حيدر",
    "assad": "أسد",
    "hussein": "حسين",
    "fadhil": "فضيل",
    "jasem": "جاسم",
    "salah": "صلاح",
    "alaa": "علاء",
    "eamd": "عماد",
    "dılar": "ديلار",
    "jafar": "جعفر",
    "karet": "كارت",
    "yousi": "يوسي",
    "bayan": "بيان",
    "issa": "عيسى",
    "hadi": "هادي",
    "theem": "ثيم",
    "di": "دي",
    "mred": "مريد",
    "jaz": "جاز",
    "sadid": "سديد",
    "alabedı": "العبيدي",
    "tahir": "طاهر",
    "çur": "شور",
    "aris": "أريس",
    "ame": "أم",
    "qassim": "قاسم",
    "çu": "شو",
    "laider": "لايدر",
    "reç": "ريش",
    "adel": "عادل",
    "çay": "شاي",
    "assim": "عصيم",
    "hu": "هو",
    "sana": "سنا",
    "eez": "عيز",
    "çuk": "شوك",
    "khudai": "خداعي",
    "mohamn": "محمن",
    "jsun": "جسون",
    "ahad": "أحد",
    "fare": "فار",
    "firas": "فراس",
    "çum": "شوم",
    "mad": "ماد",
    "emad": "عماد",
    "s": "س",
    "san": "سان",
    "karr": "كار",
    "irgan": "إرغان",
    "tav": "تاف",
    "n": "ن",
    "ilaa": "إلى",
    "mohs": "محس",
    "i": "ي",
    "ih": "إيه",
    "hakim": "حكيم",
    "tohammet": "توحمة",
    "ibak": "إيباك",
    "çub": "شوب",
    "salih": "صالح",
    "maer": "ماعر",
    "am": "أم",
    "lar": "لار",
    "nasser": "ناصر",
    "assan": "عسان",
    "asaad": "أسعد",
    "r": "ر",
    "hataf": "هاتف",
    "çat": "شات",
    "adon": "أدون",
    "tassim": "تاسيم",
    "razzaq": "رزاق",
    "ıd": "يد",
    "ned": "نيد",
    "çut": "شوت",
    "çus": "شوس",
    "earnd": "إيرند",
    "juk": "جوك",
    "alah": "آله",
    "çek": "شيك",
    "ed": "إد",
    "er": "إر",
    "husseğ": "حسين",
    "ili": "إيلي",
    "du": "دو",
    "dubur": "دبور",
    "hil": "هيل",
    "asim": "عصيم",
    "imed": "إيمد",
    
    # كلمات شائعة
    "free": "حر",
    "driver": "سائق",
    "delivery": "توصيل",
    "service": "خدمة",
}

# قاموس إضافي للأسماء الجديدة
additional_names_dict = {
    # أسماء جديدة من القائمة المقدمة
    "radhi": "رضي",
    "dayekh": "دايخ",
    "ouja": "عوجة",
    "mousa": "موسى",
    "hassa": "حسا",
    "dirgham": "دغام",
    "hameed": "حميد",
    "sadiq": "صادق",
    "yehya": "يحيى",
    "zain": "زين",
    "alabedeen": "العابدين",
    "murad": "مراد",
    "erhaeem": "إرحيم",
    "ameer": "أمير",
    "wahaam": "وهم",
    "jaber": "جابر",
    "redha": "رضا",
    "fadhel": "فضل",
    "hussam": "حسام",
    "sahib": "صاحب",
    "sanad": "سند",
    "azeez": "عزيز",
    "khudair": "خضير",
    "mujtabha": "مجتبى",
    "abdulrazzaq": "عبد الرزاق",
    "fahad": "فهد",
    "jahel": "جحل",
    "khaniyab": "خنياب",
    "rissan": "رصان",
    "karrar": "كرار",
    "adnan": "عدنان",
    "dhurgam": "ضرغام",
    "tawfiq": "توفيق",
    "kadhum": "كاظم",
    "walaa": "ولاء",
    "mohsen": "محسن",
    "shiyal": "شيال",
    "hassanein": "حسين",
    "bedewei": "بداوي",
    "thaer": "ثائر",
    "zahaa": "زهاء",
    "kazaar": "كزار",
    "zahraa": "زهراء",
    "saadon": "سعدون",
    "sawadi": "سوادي",
    "mattar": "مطر",
    "shehab": "شهاب",
    "mahmoud": "محمود",
    "hamad": "حمد",
    "tahssein": "تحسين",
    "rahi": "راحي",
}

# دمج القاموس الجديد مع القاموس الأصلي
translation_dict.update(additional_names_dict)

class BotManager:
    """فئة لإدارة عمليات البوت والمتصفح لكل مستخدم"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.driver = None
        self.is_browser_ready = False
        self.waiting_msg_id = None
        self.site_ready_msg_id = None
        self.email_msg_id = None
        self.password_msg_id = None
        self.login_process_msg_id = None
        
        # إضافة متغيرات الحالة الخاصة بالمستخدم
        self.showing_online = False
        self.showing_offline = False
        self.showing_expired = False
        self.online_count = 0
        self.offline_count = 0
        self.expired_count = 0
        self.online_users = []  # سيحتوي على قواميس تحتوي على جميع معلومات المستخدم
        self.offline_users = []  # سيحتوي على قواميس تحتوي على جميع معلومات المستخدم
        self.expired_users = []  # سيحتوي على قواميس تحتوي على جميع معلومات المستخدمين منتهي الصلاحية
        self.username = ''
        self.password = ''
        
        # متغيرات جديدة لإدارة الجلسة
        self.session_active = False
        self.last_activity = time.time()
        self.info_cache = {}  # ذاكرة تخزين مؤقتة للمعلومات
        
        # إنشاء دليل مؤقت فريد لكل مستخدم
        self.user_data_dir = tempfile.mkdtemp(prefix=f"chrome_user_{user_id}_")
        
        # ملف تخزين المستخدمين منتهي الصلاحية
        self.expired_users_file = os.path.join(self.user_data_dir, "expired_users.json")
        self.load_expired_users()
    
    def load_expired_users(self):
        """تحميل قائمة المستخدمين منتهي الصلاحية من الملف"""
        try:
            if os.path.exists(self.expired_users_file):
                with open(self.expired_users_file, 'r', encoding='utf-8') as f:
                    self.expired_users = json.load(f)
                logger.info(f"✅ تم تحميل {len(self.expired_users)} مستخدم منتهي الصلاحية للمستخدم {self.user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المستخدمين منتهي الصلاحية للمستخدم {self.user_id}: {e}")
            self.expired_users = []
    
    def save_expired_users(self):
        """حفظ قائمة المستخدمين منتهي الصلاحية في الملف"""
        try:
            with open(self.expired_users_file, 'w', encoding='utf-8') as f:
                json.dump(self.expired_users, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ تم حفظ {len(self.expired_users)} مستخدم منتهي الصلاحية للمستخدم {self.user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ المستخدمين منتهي الصلاحية للمستخدم {self.user_id}: {e}")
    
    def init_browser(self):
        """تهيئة المتصفح مع تحسينات لضمان الاتصال"""
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--headless')  # تشغيل في الخلفية
            
            # إضافة دليل ملف تعريف المستخدم الفريد لكل مستخدم
            chrome_options.add_argument(f'--user-data-dir={self.user_data_dir}')
            
            # إضافة خيارات إضافية للعزل
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            
            # إضافة خيارات لتحسين الاتصال
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--allow-cross-origin-auth-prompt')
            
            # إضافة هذه الأسطر للتعامل مع بيئة النشر
            chrome_options.add_argument('--remote-debugging-port=9222')
            chrome_options.add_argument('--disable-setuid-sandbox')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(60)  # 60 ثانية مهلة لتحميل الصفحة
            
            # محاولة فتح الموقع مع إعادة المحاولة
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 محاولة فتح الموقع للمستخدم {self.user_id} - المحاولة {attempt + 1}")
                    self.driver.get("https://merchant.totersapp.com/#/")
                    
                    # انتظار تحميل الصفحة بشكل كامل
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # انتظار إضافي لضمان تحميل جميع العناصر الديناميكية
                    time.sleep(5)
                    
                    # التحقق من أن الصفحة تحملت بشكل صحيح
                    if "merchant.totersapp.com" in self.driver.current_url:
                        logger.info(f"✅ تم فتح الموقع بنجاح للمستخدم {self.user_id}")
                        self.is_browser_ready = True
                        self.session_active = True
                        self.last_activity = time.time()
                        return True
                    else:
                        logger.warning(f"⚠️ تم التوجيه إلى صفحة أخرى للمستخدم {self.user_id}")
                except Exception as e:
                    logger.error(f"❌ فشل محاولة {attempt + 1} لفتح الموقع للمستخدم {self.user_id}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)  # انتظار قبل إعادة المحاولة
            
            # إذا فشلت جميع المحاولات
            logger.error(f"❌ فشل في فتح الموقع بعد {max_retries} محاولات للمستخدم {self.user_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة المتصفح للمستخدم {self.user_id}: {e}")
            # في حالة الفشل، تأكد من تنظيف أي موارد تم إنشاؤها
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            return False
    
    def close_browser(self):
        """إغلاق المتصفح"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info(f"✅ تم إغلاق المتصفح للمستخدم {self.user_id}")
            except Exception as e:
                logger.error(f"❌ خطأ في إغلاق المتصفح للمستخدم {self.user_id}: {e}")
            finally:
                self.driver = None
                self.is_browser_ready = False
                self.session_active = False
        
        # حذف الدليل المؤقت
        try:
            if os.path.exists(self.user_data_dir):
                import shutil
                shutil.rmtree(self.user_data_dir)
                logger.info(f"✅ تم حذف الدليل المؤقت للمستخدم {self.user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في حذف الدليل المؤقت للمستخدم {self.user_id}: {e}")
    
    def reset_state(self):
        """إعادة تعيين حالة المستخدم"""
        self.showing_online = False
        self.showing_offline = False
        self.showing_expired = False
        self.online_count = 0
        self.offline_count = 0
        self.expired_count = 0
        self.online_users = []
        self.offline_users = []
        self.expired_users = []
        self.info_cache.clear()  # مسح الذاكرة المؤقتة

# ====== دوال مساعدة ======
def get_bot_manager(user_id):
    """إنشاء أو الحصول على مدير البوت للمستخدم المحدد"""
    if user_id not in users_data:
        users_data[user_id] = BotManager(user_id)
    
    # تحديث وقت النشاط
    users_data[user_id].last_activity = time.time()
    return users_data[user_id]

def translate_name(name):
    """ترجمة الاسم بين العربية والإنجليزية مع استخراج الاسم الأول والثاني فقط"""
    try:
        # تنظيف الاسم وإزالة النقاط والكلمات غير المرغوب فيها
        cleaned_name = re.sub(r'\.\.\.|\.|\bfree\b', '', name, flags=re.IGNORECASE).strip()
        
        # تقسيم الاسم إلى كلمات
        words = cleaned_name.split()
        
        # أخذ أول كلمتين فقط (الاسم الأول والثاني)
        if len(words) >= 2:
            short_name = f"{words[0]} {words[1]}"
        else:
            short_name = words[0] if words else name
        
        # محاولة ترجمة الكلمات
        translated_words = []
        for word in short_name.split():
            # البحث عن الترجمة في القاموس (بالحالة الصغيرة للتطابق)
            lower_word = word.lower()
            if lower_word in translation_dict:
                translated_words.append(translation_dict[lower_word])
            else:
                # إذا لم توجد ترجمة، نترك الكلمة كما هي
                translated_words.append(word)
        
        # دمج الكلمات المترجمة
        translated_name = " ".join(translated_words)
        
        # إذا كان الاسم الأصلي بالعربية والترجمة بالإنجليزية أو العكس
        # نعرض الاسم باللغتين إذا كان مختلفاً
        if short_name != translated_name:
            return f"{short_name}\n{translated_name}"
        else:
            return short_name
            
    except Exception as e:
        logger.error(f"خطأ في ترجمة الاسم {name}: {e}")
        return name

# ====== دوال إنشاء الأزرار ======
def create_main_keyboard(bot_manager):
    """إنشاء لوحة المفاتيح الرئيسية"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🟢 Online ({bot_manager.online_count})", callback_data="online_info"),
            InlineKeyboardButton(f"🔴 Offline ({bot_manager.offline_count})", callback_data="offline_info")
        ],
        [
            InlineKeyboardButton(f"⏰ منتهي الصلاحية ({bot_manager.expired_count})", callback_data="expired_info")
        ],
        [InlineKeyboardButton("🔄 تحديث", callback_data="refresh_data")]
    ])

def create_users_keyboard(users_list, user_type, bot_manager):
    """إنشاء لوحة مفاتيح لقائمة المستخدمين - زر واحد في كل صف"""
    keyboard = []
    
    for i, user in enumerate(users_list):
        # استخراج الاسم من قاموس المستخدم
        name = user['name'] if isinstance(user, dict) else user
        
        # ترجمة الاسم وعرض الاسم الأول والثاني فقط
        translated_name = translate_name(name)
        
        # زيادة الحد الأقصى للأحرف المعروضة
        if len(translated_name) > 40:
            display_name = translated_name[:37] + "..."
        else:
            display_name = translated_name
            
        # كل زر في صف منفصل (صف واحد لكل زر)
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"user_{user_type}_{i}")])
    
    # إضافة أزرار التحكم في صف واحد
    keyboard.append([
        InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"),
        InlineKeyboardButton("🔄 تحديث", callback_data="refresh_data")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_online_user_options_keyboard(user_index, bot_manager):
    """إنشاء لوحة مفاتيح لخيارات المستخدم المتصل"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 الرقم", callback_data=f"online_phone_{user_index}")],
        [InlineKeyboardButton("📅 تاريخ اخر طلب", callback_data=f"online_last_order_{user_index}")],
        [InlineKeyboardButton("💰 محفظة الكابتن", callback_data=f"online_captain_wallet_{user_index}")],
        [InlineKeyboardButton("👤 الاسم الكامل", callback_data=f"online_full_name_{user_index}")],
        [InlineKeyboardButton("⏰ انقل لمنتهي الصلاحية", callback_data=f"online_to_expired_{user_index}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"online_back_to_list_{user_index}")]
    ])

def create_offline_user_options_keyboard(user_index, bot_manager):
    """إنشاء لوحة مفاتيح لخيارات المستخدم غير المتصل"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 الرقم", callback_data=f"offline_phone_{user_index}")],
        [InlineKeyboardButton("📅 تاريخ اخر طلب", callback_data=f"offline_last_order_{user_index}")],
        [InlineKeyboardButton("📊 عدد الطلبات", callback_data=f"offline_order_count_{user_index}")],
        [InlineKeyboardButton("💰 محفظة الكابتن", callback_data=f"offline_captain_wallet_{user_index}")],
        [InlineKeyboardButton("👤 الاسم الكامل", callback_data=f"offline_full_name_{user_index}")],
        [InlineKeyboardButton("⏰ انقل لمنتهي الصلاحية", callback_data=f"offline_to_expired_{user_index}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"offline_back_to_list_{user_index}")]
    ])

def create_expired_user_options_keyboard(user_index, bot_manager):
    """إنشاء لوحة مفاتيح لخيارات المستخدم منتهي الصلاحية"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 الرقم", callback_data=f"expired_phone_{user_index}")],
        [InlineKeyboardButton("📅 تاريخ اخر طلب", callback_data=f"expired_last_order_{user_index}")],
        [InlineKeyboardButton("📊 عدد الطلبات", callback_data=f"expired_order_count_{user_index}")],
        [InlineKeyboardButton("💰 محفظة الكابتن", callback_data=f"expired_captain_wallet_{user_index}")],
        [InlineKeyboardButton("👤 الاسم الكامل", callback_data=f"expired_full_name_{user_index}")],
        [InlineKeyboardButton("↩️ ارجع للأقسام العادية", callback_data=f"expired_to_normal_{user_index}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"expired_back_to_list_{user_index}")]
    ])

# ====== دوال للحصول على معلومات المستخدم ======
async def get_user_info_optimized(user_index, is_online, user_id):
    """الحصول على معلومات المستخدم بشكل محسن"""
    bot_manager = get_bot_manager(user_id)
    
    try:
        # التحقق من وجود المعلومات في الذاكرة المؤقتة
        cache_key = f"{user_index}_{is_online}"
        if cache_key in bot_manager.info_cache:
            return bot_manager.info_cache[cache_key]
        
        # الحصول على قائمة المستخدمين المناسبة
        if is_online == "expired":
            users_list = bot_manager.expired_users
        elif is_online:
            users_list = bot_manager.online_users
        else:
            users_list = bot_manager.offline_users
        
        # التحقق من وجود المستخدم
        if user_index >= len(users_list):
            return None
        
        user = users_list[user_index]
        
        # إذا كانت المعلومات موجودة بالفعل في القائمة، نعيدها مباشرة
        if isinstance(user, dict) and all(key in user for key in ['name', 'phone', 'last_order', 'order_count', 'captain_wallet', 'full_name']):
            bot_manager.info_cache[cache_key] = user
            return user
        
        # إذا لم تكن المعلومات موجودة، نقوم بجلبها من الموقع
        if not bot_manager.is_browser_ready or not bot_manager.driver:
            return None
        
        # في هذه الحالة، نعيد المعلومات المتوفرة فقط
        result = {
            'name': user.get('name', 'غير متوفر'),
            'phone': 'غير متوفر',
            'last_order': 'غير متوفر',
            'order_count': 'غير متوفر',
            'captain_wallet': 'غير متوفر',
            'full_name': 'غير متوفر'
        }
        
        # حفظ النتيجة في الذاكرة المؤقتة
        bot_manager.info_cache[cache_key] = result
        return result
        
    except Exception as e:
        logger.error(f"❌ خطأ في الحصول على معلومات المستخدم {user_index}: {e}")
        return None

# ====== معالجات البوت ======
async def on_start(app):
    """الدالة التي تنفذ عند بدء تشغيل البوت"""
    logger.info("🚀 تم بدء تشغيل البوت بنجاح")
    # بدء مجدول تنظيف الجلسات
    start_cleanup_scheduler()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر البدء - عرض زر تسجيل الدخول"""
    user_id = update.effective_user.id
    
    # إنشاء لوحة مفاتيح تحتوي على زر تسجيل الدخول
    keyboard = [[InlineKeyboardButton("تسجيل دخول", callback_data="login_pressed")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # إرسال رسالة الترحيب مع الزر
    await update.message.reply_text(
        text="مرحباً بك في أداة إدارة المستخدمين!\n\nللبدء، يرجى الضغط على زر تسجيل الدخول أدناه:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أزرار الإنلاين"""
    query = update.callback_query
    user_id = query.from_user.id
    bot_manager = get_bot_manager(user_id)
    
    # تحديث وقت النشاط
    bot_manager.last_activity = time.time()
    
    await query.answer()
    
    if query.data == "login_pressed":
        # حذف رسالة زر تسجيل الدخول
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=query.message.message_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة تسجيل الدخول للمستخدم {user_id}: {e}")
        
        # إرسال رسالة انتظار أولية
        waiting_msg = await query.message.reply_text(
            text="🔄 جاري فتح الموقع...\nيرجى الانتظار حتى يكتمل التحميل"
        )
        bot_manager.waiting_msg_id = waiting_msg.message_id
        
        # تهيئة المتصفح في خيط منفصل
        loop = asyncio.get_event_loop()
        browser_ready = await loop.run_in_executor(executor, bot_manager.init_browser)
        
        # حذف رسالة الانتظار
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.waiting_msg_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة الانتظار للمستخدم {user_id}: {e}")
        
        if browser_ready:
            # إرسال رسالة تأكيد مع زر Start
            keyboard = [[InlineKeyboardButton("بدء التسجيل", callback_data="start_pressed")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            site_ready_msg = await query.message.reply_text(
                text="✅ تم فتح الموقع بنجاح!\n\nلبدء تسجيل الدخول اضغط على الزر أدناه:",
                reply_markup=reply_markup
            )
            bot_manager.site_ready_msg_id = site_ready_msg.message_id
        else:
            await query.message.reply_text(
                text="❌ فشل في تحضير المتصفح. يرجى المحاولة لاحقاً"
            )
    
    elif query.data == "start_pressed":
        # حذف رسالة تأكيد فتح الموقع
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.site_ready_msg_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة التأكيد للمستخدم {user_id}: {e}")
        
        # إرسال رسالة طلب الإيميل
        email_msg = await query.message.reply_text(
            text="📧 يرجى إرسال الإيميل الخاص بك:"
        )
        bot_manager.email_msg_id = email_msg.message_id
        return USERNAME
    
    elif query.data == "online_info":
        if bot_manager.showing_online:
            # إخفاء الأسماء إذا كانت معروضة
            bot_manager.showing_online = False
            keyboard = create_main_keyboard(bot_manager)
            await query.edit_message_text(
                text="✅ تم تسجيل الدخول بنجاح!",
                reply_markup=keyboard
            )
        else:
            # عرض أسماء المستخدمين المتصلين من البيانات المخزنة
            bot_manager.showing_online = True
            bot_manager.showing_offline = False
            bot_manager.showing_expired = False
            
            if bot_manager.online_count > 0 and bot_manager.online_users:
                # عرض الأسماء مباشرة من البيانات المخزنة
                keyboard = create_users_keyboard(bot_manager.online_users, "online", bot_manager)
                await query.edit_message_text(
                    text=f"🟢 قائمة المستخدمين المتصلين ({bot_manager.online_count}):",
                    reply_markup=keyboard
                )
            else:
                await query.answer("ℹ️ لا يوجد مستخدمين متصلين حالياً", show_alert=True)
    
    elif query.data == "offline_info":
        if bot_manager.showing_offline:
            # إخفاء الأسماء إذا كانت معروضة
            bot_manager.showing_offline = False
            keyboard = create_main_keyboard(bot_manager)
            await query.edit_message_text(
                text="✅ تم تسجيل الدخول بنجاح!",
                reply_markup=keyboard
            )
        else:
            # عرض أسماء المستخدمين غير المتصلين من البيانات المخزنة
            bot_manager.showing_offline = True
            bot_manager.showing_online = False
            bot_manager.showing_expired = False
            
            if bot_manager.offline_count > 0 and bot_manager.offline_users:
                # عرض الأسماء مباشرة من البيانات المخزنة
                keyboard = create_users_keyboard(bot_manager.offline_users, "offline", bot_manager)
                await query.edit_message_text(
                    text=f"🔴 قائمة المستخدمين غير المتصلين ({bot_manager.offline_count}):",
                    reply_markup=keyboard
                )
            else:
                await query.answer("ℹ️ لا يوجد مستخدمين غير متصلين حالياً", show_alert=True)
    
    elif query.data == "expired_info":
        if bot_manager.showing_expired:
            # إخفاء الأسماء إذا كانت معروضة
            bot_manager.showing_expired = False
            keyboard = create_main_keyboard(bot_manager)
            await query.edit_message_text(
                text="✅ تم تسجيل الدخول بنجاح!",
                reply_markup=keyboard
            )
        else:
            # عرض أسماء المستخدمين منتهي الصلاحية من البيانات المخزنة
            bot_manager.showing_expired = True
            bot_manager.showing_online = False
            bot_manager.showing_offline = False
            
            if bot_manager.expired_count > 0 and bot_manager.expired_users:
                # عرض الأسماء مباشرة من البيانات المخزنة
                keyboard = create_users_keyboard(bot_manager.expired_users, "expired", bot_manager)
                await query.edit_message_text(
                    text=f"⏰ قائمة المستخدمين منتهي الصلاحية ({bot_manager.expired_count}):",
                    reply_markup=keyboard
                )
            else:
                await query.answer("ℹ️ لا يوجد مستخدمين منتهي الصلاحية حالياً", show_alert=True)
    
    elif query.data == "back_to_main":
        # العودة إلى القائمة الرئيسية
        bot_manager.showing_online = False
        bot_manager.showing_offline = False
        bot_manager.showing_expired = False
        keyboard = create_main_keyboard(bot_manager)
        await query.edit_message_text(
            text="✅ تم تسجيل الدخول بنجاح!",
            reply_markup=keyboard
        )
    
    elif query.data == "refresh_data":
        # تحديث البيانات
        await query.answer("🔄 جاري تحديث البيانات...")
        
        # إعادة تعيين الحالة
        bot_manager.reset_state()
        
        # العودة إلى القائمة الرئيسية مع تحديث الأعداد
        keyboard = create_main_keyboard(bot_manager)
        await query.edit_message_text(
            text="✅ تم تسجيل الدخول بنجاح!",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("user_online_"):
        # معالجة النقر على اسم مستخدم متصل - عرض الخيارات
        user_index = int(query.data.split("_")[-1])
        user_name = bot_manager.online_users[user_index]['name']
        translated_name = translate_name(user_name)
        
        # إنشاء لوحة أزرار الخيارات
        keyboard = create_online_user_options_keyboard(user_index, bot_manager)
        await query.edit_message_text(
            text=f"👤 تفاصيل المستخدم: {translated_name}\n\nيرجى اختيار المعلومات المطلوبة:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("user_offline_"):
        # معالجة النقر على اسم مستخدم غير متصل - عرض الخيارات
        user_index = int(query.data.split("_")[-1])
        user_name = bot_manager.offline_users[user_index]['name']
        translated_name = translate_name(user_name)
        
        # إنشاء لوحة أزرار الخيارات
        keyboard = create_offline_user_options_keyboard(user_index, bot_manager)
        await query.edit_message_text(
            text=f"👤 تفاصيل المستخدم: {translated_name}\n\nيرجى اختيار المعلومات المطلوبة:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("user_expired_"):
        # معالجة النقر على اسم مستخدم منتهي الصلاحية - عرض الخيارات
        user_index = int(query.data.split("_")[-1])
        user_name = bot_manager.expired_users[user_index]['name']
        translated_name = translate_name(user_name)
        
        # إنشاء لوحة أزرار الخيارات
        keyboard = create_expired_user_options_keyboard(user_index, bot_manager)
        await query.edit_message_text(
            text=f"👤 تفاصيل المستخدم: {translated_name}\n\nيرجى اختيار المعلومات المطلوبة:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("online_phone_"):
        # عرض زر يحتوي على رقم الهاتف
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, True, user_id)
        if user_info:
            phone = user_info.get('phone', 'غير متوفر')
            # إنشاء زر يحتوي على رقم الهاتف
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📞 {phone}", callback_data=f"send_phone_{user_index}_online")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"online_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📞 رقم الهاتف:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على رقم الهاتف", show_alert=True)
    
    elif query.data.startswith("offline_phone_"):
        # عرض زر يحتوي على رقم الهاتف
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, False, user_id)
        if user_info:
            phone = user_info.get('phone', 'غير متوفر')
            # إنشاء زر يحتوي على رقم الهاتف
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📞 {phone}", callback_data=f"send_phone_{user_index}_offline")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"offline_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📞 رقم الهاتف:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على رقم الهاتف", show_alert=True)
    
    elif query.data.startswith("expired_phone_"):
        # عرض زر يحتوي على رقم الهاتف
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, "expired", user_id)
        if user_info:
            phone = user_info.get('phone', 'غير متوفر')
            # إنشاء زر يحتوي على رقم الهاتف
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📞 {phone}", callback_data=f"send_phone_{user_index}_expired")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"expired_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📞 رقم الهاتف:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على رقم الهاتف", show_alert=True)
    
    elif query.data.startswith("send_phone_"):
        # إرسال الرقم كرسالة نصية
        parts = query.data.split("_")
        user_index = int(parts[2])
        user_type = parts[3]
        
        # الحصول على معلومات المستخدم
        if user_type == "online":
            user_info = await get_user_info_optimized(user_index, True, user_id)
        elif user_type == "offline":
            user_info = await get_user_info_optimized(user_index, False, user_id)
        else:  # expired
            user_info = await get_user_info_optimized(user_index, "expired", user_id)
        
        if user_info:
            phone = user_info.get('phone', 'غير متوفر')
            # إرسال الرقم كرسالة نصية
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📞 رقم الهاتف: {phone}"
            )
            await query.answer("✅ تم إرسال رقم الهاتف")
        else:
            await query.answer("❌ لم يتم العثور على رقم الهاتف", show_alert=True)
    
    elif query.data.startswith("online_last_order_"):
        # عرض زر يحتوي على تاريخ آخر طلب
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, True, user_id)
        if user_info:
            last_order = user_info.get('last_order', 'غير متوفر')
            # إنشاء زر يحتوي على تاريخ آخر طلب
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📅 {last_order}", callback_data=f"online_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"online_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📅 تاريخ آخر طلب:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على تاريخ آخر طلب", show_alert=True)
    
    elif query.data.startswith("offline_last_order_"):
        # عرض زر يحتوي على تاريخ آخر طلب
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, False, user_id)
        if user_info:
            last_order = user_info.get('last_order', 'غير متوفر')
            # إنشاء زر يحتوي على تاريخ آخر طلب
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📅 {last_order}", callback_data=f"offline_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"offline_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📅 تاريخ آخر طلب:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على تاريخ آخر طلب", show_alert=True)
    
    elif query.data.startswith("expired_last_order_"):
        # عرض زر يحتوي على تاريخ آخر طلب
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, "expired", user_id)
        if user_info:
            last_order = user_info.get('last_order', 'غير متوفر')
            # إنشاء زر يحتوي على تاريخ آخر طلب
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📅 {last_order}", callback_data=f"expired_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"expired_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📅 تاريخ آخر طلب:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على تاريخ آخر طلب", show_alert=True)
    
    elif query.data.startswith("online_order_count_"):
        # عرض زر يحتوي على عدد الطلبات
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, True, user_id)
        if user_info:
            order_count = user_info.get('order_count', 'غير متوفر')
            # إنشاء زر يحتوي على عدد الطلبات
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📊 {order_count}", callback_data=f"online_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"online_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📊 عدد الطلبات:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على عدد الطلبات", show_alert=True)
    
    elif query.data.startswith("offline_order_count_"):
        # عرض زر يحتوي على عدد الطلبات
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, False, user_id)
        if user_info:
            order_count = user_info.get('order_count', 'غير متوفر')
            # إنشاء زر يحتوي على عدد الطلبات
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📊 {order_count}", callback_data=f"offline_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"offline_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📊 عدد الطلبات:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على عدد الطلبات", show_alert=True)
    
    elif query.data.startswith("expired_order_count_"):
        # عرض زر يحتوي على عدد الطلبات
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, "expired", user_id)
        if user_info:
            order_count = user_info.get('order_count', 'غير متوفر')
            # إنشاء زر يحتوي على عدد الطلبات
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📊 {order_count}", callback_data=f"expired_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"expired_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="📊 عدد الطلبات:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على عدد الطلبات", show_alert=True)
    
    elif query.data.startswith("online_captain_wallet_"):
        # عرض زر يحتوي على محفظة الكابتن
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, True, user_id)
        if user_info:
            wallet = user_info.get('captain_wallet', 'غير متوفر')
            # إنشاء زر يحتوي على محفظة الكابتن
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💰 {wallet} د.ع", callback_data=f"online_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"online_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="💰 محفظة الكابتن:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على محفظة الكابتن", show_alert=True)
    
    elif query.data.startswith("offline_captain_wallet_"):
        # عرض زر يحتوي على محفظة الكابتن
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, False, user_id)
        if user_info:
            wallet = user_info.get('captain_wallet', 'غير متوفر')
            # إنشاء زر يحتوي على محفظة الكابتن
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💰 {wallet} د.ع", callback_data=f"offline_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"offline_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="💰 محفظة الكابتن:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على محفظة الكابتن", show_alert=True)
    
    elif query.data.startswith("expired_captain_wallet_"):
        # عرض زر يحتوي على محفظة الكابتن
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, "expired", user_id)
        if user_info:
            wallet = user_info.get('captain_wallet', 'غير متوفر')
            # إنشاء زر يحتوي على محفظة الكابتن
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💰 {wallet} د.ع", callback_data=f"expired_back_to_options_{user_index}")],
                [InlineKeyboardButton("⬅️ رجوع", callback_data=f"expired_back_to_options_{user_index}")]
            ])
            await query.edit_message_text(
                text="💰 محفظة الكابتن:",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ لم يتم العثور على محفظة الكابتن", show_alert=True)
    
    elif query.data.startswith("online_full_name_"):
        # إرسال الاسم الكامل كرسالة نصية
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, True, user_id)
        if user_info:
            full_name = user_info.get('full_name', 'غير متوفر')
            # إرسال الاسم كرسالة نصية
            await context.bot.send_message(
                chat_id=user_id,
                text=f"👤 الاسم الكامل: {full_name}"
            )
            await query.answer("✅ تم إرسال الاسم الكامل")
        else:
            await query.answer("❌ لم يتم العثور على الاسم الكامل", show_alert=True)
    
    elif query.data.startswith("offline_full_name_"):
        # إرسال الاسم الكامل كرسالة نصية
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, False, user_id)
        if user_info:
            full_name = user_info.get('full_name', 'غير متوفر')
            # إرسال الاسم كرسالة نصية
            await context.bot.send_message(
                chat_id=user_id,
                text=f"👤 الاسم الكامل: {full_name}"
            )
            await query.answer("✅ تم إرسال الاسم الكامل")
        else:
            await query.answer("❌ لم يتم العثور على الاسم الكامل", show_alert=True)
    
    elif query.data.startswith("expired_full_name_"):
        # إرسال الاسم الكامل كرسالة نصية
        user_index = int(query.data.split("_")[-1])
        user_info = await get_user_info_optimized(user_index, "expired", user_id)
        if user_info:
            full_name = user_info.get('full_name', 'غير متوفر')
            # إرسال الاسم كرسالة نصية
            await context.bot.send_message(
                chat_id=user_id,
                text=f"👤 الاسم الكامل: {full_name}"
            )
            await query.answer("✅ تم إرسال الاسم الكامل")
        else:
            await query.answer("❌ لم يتم العثور على الاسم الكامل", show_alert=True)
    
    elif query.data.startswith("online_to_expired_"):
        # نقل مستخدم متصل إلى قسم منتهي الصلاحية
        user_index = int(query.data.split("_")[-1])
        user_info = bot_manager.online_users[user_index]
        
        # إضافة المستخدم إلى قائمة منتهي الصلاحية
        bot_manager.expired_users.append(user_info)
        bot_manager.expired_count = len(bot_manager.expired_users)
        
        # حذف المستخدم من قائمة المتصلين
        bot_manager.online_users.pop(user_index)
        bot_manager.online_count = len(bot_manager.online_users)
        
        # حفظ التغييرات
        bot_manager.save_expired_users()
        
        # إرسال تأكيد
        await query.answer("✅ تم نقل المستخدم إلى قسم منتهي الصلاحية")
        
        # العودة إلى قائمة المستخدمين المتصلين
        keyboard = create_users_keyboard(bot_manager.online_users, "online", bot_manager)
        await query.edit_message_text(
            text=f"🟢 قائمة المستخدمين المتصلين ({bot_manager.online_count}):",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("offline_to_expired_"):
        # نقل مستخدم غير متصل إلى قسم منتهي الصلاحية
        user_index = int(query.data.split("_")[-1])
        user_info = bot_manager.offline_users[user_index]
        
        # إضافة المستخدم إلى قائمة منتهي الصلاحية
        bot_manager.expired_users.append(user_info)
        bot_manager.expired_count = len(bot_manager.expired_users)
        
        # حذف المستخدم من قائمة غير المتصلين
        bot_manager.offline_users.pop(user_index)
        bot_manager.offline_count = len(bot_manager.offline_users)
        
        # حفظ التغييرات
        bot_manager.save_expired_users()
        
        # إرسال تأكيد
        await query.answer("✅ تم نقل المستخدم إلى قسم منتهي الصلاحية")
        
        # العودة إلى قائمة المستخدمين غير المتصلين
        keyboard = create_users_keyboard(bot_manager.offline_users, "offline", bot_manager)
        await query.edit_message_text(
            text=f"🔴 قائمة المستخدمين غير المتصلين ({bot_manager.offline_count}):",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("expired_to_normal_"):
        # نقل مستخدم منتهي الصلاحية إلى الأقسام العادية
        user_index = int(query.data.split("_")[-1])
        user_info = bot_manager.expired_users[user_index]
        
        # تحديد ما إذا كان المستخدم متصلاً أم غير متصل بناءً على البيانات المخزنة
        # في هذا المثال، سنضيف المستخدم إلى قائمة غير المتصلين بشكل افتراضي
        # يمكن تعديل هذا الجزء لتحديد الحالة بناءً على بيانات أخرى
        bot_manager.offline_users.append(user_info)
        bot_manager.offline_count = len(bot_manager.offline_users)
        
        # حذف المستخدم من قائمة منتهي الصلاحية
        bot_manager.expired_users.pop(user_index)
        bot_manager.expired_count = len(bot_manager.expired_users)
        
        # حفظ التغييرات
        bot_manager.save_expired_users()
        
        # إرسال تأكيد
        await query.answer("✅ تم إرجاع المستخدم إلى الأقسام العادية")
        
        # العودة إلى قائمة المستخدمين منتهي الصلاحية
        keyboard = create_users_keyboard(bot_manager.expired_users, "expired", bot_manager)
        await query.edit_message_text(
            text=f"⏰ قائمة المستخدمين منتهي الصلاحية ({bot_manager.expired_count}):",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("online_back_to_options_"):
        # العودة إلى خيارات المستخدم المتصل
        user_index = int(query.data.split("_")[-1])
        user_name = bot_manager.online_users[user_index]['name']
        translated_name = translate_name(user_name)
        
        # إنشاء لوحة أزرار الخيارات
        keyboard = create_online_user_options_keyboard(user_index, bot_manager)
        await query.edit_message_text(
            text=f"👤 تفاصيل المستخدم: {translated_name}\n\nيرجى اختيار المعلومات المطلوبة:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("offline_back_to_options_"):
        # العودة إلى خيارات المستخدم غير المتصل
        user_index = int(query.data.split("_")[-1])
        user_name = bot_manager.offline_users[user_index]['name']
        translated_name = translate_name(user_name)
        
        # إنشاء لوحة أزرار الخيارات
        keyboard = create_offline_user_options_keyboard(user_index, bot_manager)
        await query.edit_message_text(
            text=f"👤 تفاصيل المستخدم: {translated_name}\n\nيرجى اختيار المعلومات المطلوبة:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("expired_back_to_options_"):
        # العودة إلى خيارات المستخدم منتهي الصلاحية
        user_index = int(query.data.split("_")[-1])
        user_name = bot_manager.expired_users[user_index]['name']
        translated_name = translate_name(user_name)
        
        # إنشاء لوحة أزرار الخيارات
        keyboard = create_expired_user_options_keyboard(user_index, bot_manager)
        await query.edit_message_text(
            text=f"👤 تفاصيل المستخدم: {translated_name}\n\nيرجى اختيار المعلومات المطلوبة:",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("online_back_to_list_"):
        # العودة إلى قائمة المستخدمين المتصلين
        user_index = int(query.data.split("_")[-1])
        keyboard = create_users_keyboard(bot_manager.online_users, "online", bot_manager)
        await query.edit_message_text(
            text=f"🟢 قائمة المستخدمين المتصلين ({bot_manager.online_count}):",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("offline_back_to_list_"):
        # العودة إلى قائمة المستخدمين غير المتصلين
        user_index = int(query.data.split("_")[-1])
        keyboard = create_users_keyboard(bot_manager.offline_users, "offline", bot_manager)
        await query.edit_message_text(
            text=f"🔴 قائمة المستخدمين غير المتصلين ({bot_manager.offline_count}):",
            reply_markup=keyboard
        )
    
    elif query.data.startswith("expired_back_to_list_"):
        # العودة إلى قائمة المستخدمين منتهي الصلاحية
        user_index = int(query.data.split("_")[-1])
        keyboard = create_users_keyboard(bot_manager.expired_users, "expired", bot_manager)
        await query.edit_message_text(
            text=f"⏰ قائمة المستخدمين منتهي الصلاحية ({bot_manager.expired_count}):",
            reply_markup=keyboard
        )
    
    return ConversationHandler.END

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    user_id = update.effective_user.id
    bot_manager = get_bot_manager(user_id)
    
    # تحديث وقت النشاط
    bot_manager.last_activity = time.time()
    
    text = update.message.text
    
    # التحقق من أن المستخدم في حالة تسجيل الدخول
    if bot_manager.email_msg_id is not None:
        # تخزين الإيميل
        bot_manager.username = text
        
        # حذف رسالة طلب الإيميل
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.email_msg_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة طلب الإيميل للمستخدم {user_id}: {e}")
        
        # إرسال رسالة طلب كلمة المرور
        password_msg = await update.message.reply_text(
            text="🔐 يرجى إرسال كلمة المرور الخاصة بك:"
        )
        bot_manager.password_msg_id = password_msg.message_id
        bot_manager.email_msg_id = None
        
        return PASSWORD
    
    elif bot_manager.password_msg_id is not None:
        # تخزين كلمة المرور
        bot_manager.password = text
        
        # حذف رسالة طلب كلمة المرور
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.password_msg_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة طلب كلمة المرور للمستخدم {user_id}: {e}")
        
        # إرسال رسالة انتظار لتسجيل الدخول
        login_process_msg = await update.message.reply_text(
            text="🔄 جاري تسجيل الدخول...\nيرجى الانتظار"
        )
        bot_manager.login_process_msg_id = login_process_msg.message_id
        bot_manager.password_msg_id = None
        
        # تسجيل الدخول في خيط منفصل
        loop = asyncio.get_event_loop()
        login_success = await loop.run_in_executor(executor, bot_manager.login_to_site)
        
        # حذف رسالة الانتظار
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.login_process_msg_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة الانتظار للمستخدم {user_id}: {e}")
        
        if login_success:
            # إرسال رسالة تأكيد مع القائمة الرئيسية
            keyboard = create_main_keyboard(bot_manager)
            await update.message.reply_text(
                text="✅ تم تسجيل الدخول بنجاح!",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text="❌ فشل في تسجيل الدخول. يرجى التحقق من بيانات الاعتماد والمحاولة مرة أخرى"
            )
        
        return ConversationHandler.END
    
    # رسالة غير معروفة
    await update.message.reply_text(
        text="❌ لم يتم فهم الرسالة. يرجى استخدام الأزرار المتاحة."
    )

# ====== دوال مساعدة إضافية ======
def start_cleanup_scheduler():
    """بدء مجدول تنظيف الجلسات غير النشطة"""
    import threading
    
    def cleanup_sessions():
        """تنظيف الجلسات غير النشطة"""
        while True:
            time.sleep(60 * 5)  # التحقق كل 5 دقائق
            
            current_time = time.time()
            with session_lock:
                # إنشاء قائمة من معرفات المستخدمين الذين تم انتهاء جلساتهم
                expired_sessions = []
                for user_id, bot_manager in users_data.items():
                    if current_time - bot_manager.last_activity > SESSION_TIMEOUT:
                        expired_sessions.append(user_id)
                
                # إغلاق الجلسات المنتهية
                for user_id in expired_sessions:
                    logger.info(f"🧹 تنظيف جلسة المستخدم {user_id} بسبب عدم النشاط")
                    users_data[user_id].close_browser()
                    del users_data[user_id]
    
    # بدء الخيط في الخلفية
    cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
    cleanup_thread.start()

# ====== الدالة الرئيسية ======
def main():
    """الدالة الرئيسية لتشغيل البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start_command))
    
    # إضافة معالج المحادثة لتسجيل الدخول
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^start_pressed$")],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)]
        },
        fallbacks=[],
        per_message=False
    )
    application.add_handler(conv_handler)
    
    # إضافة معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # إضافة معالج الرسائل العامة
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # إضافة دالة البدء
    application.job_queue.run_once(on_start, when=1)
    
    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()

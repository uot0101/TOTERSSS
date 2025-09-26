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
MAX_CONCURRENT_TASKS = 100
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
    
    elif query.data == "refresh_data":
        # تحديث البيانات
        await query.answer("🔄 جاري تحديث البيانات...")
        
        # إرسال رسالة انتظار
        waiting_msg = await query.message.reply_text("⏳ جاري تحديث البيانات من الموقع، يرجى الانتظار...")
        
        # تنفيذ عملية التحديث
        success = await refresh_user_data(user_id)
        
        # حذف رسالة الانتظار
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=waiting_msg.message_id)
        except Exception as e:
            logger.error(f"خطأ في حذف رسالة الانتظار للمستخدم {user_id}: {e}")
        
        if success:
            keyboard = create_main_keyboard(bot_manager)
            await query.edit_message_text(
                text="✅ تم تحديث البيانات بنجاح!",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ فشل في تحديث البيانات", show_alert=True)
            # إعادة عرض القائمة الرئيسية مع البيانات القديمة
            keyboard = create_main_keyboard(bot_manager)
            await query.edit_message_text(
                text="⚠️ فشل تحديث البيانات، يتم عرض البيانات المخزنة مسبقاً",
                reply_markup=keyboard
            )
    
    return ConversationHandler.END

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الحصول على اسم المستخدم"""
    user_id = update.effective_user.id
    bot_manager = get_bot_manager(user_id)
    
    username = update.message.text.strip()
    bot_manager.username = username
    
    # حذف رسالة طلب الإيميل
    try:
        await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.email_msg_id)
    except Exception as e:
        logger.error(f"خطأ في حذف رسالة طلب الإيميل للمستخدم {user_id}: {e}")
    
    # إرسال رسالة طلب كلمة المرور
    password_msg = await update.message.reply_text(
        text=f"✅ تم حفظ الإيميل: {username}\n\n🔒 يرجى إرسال كلمة المرور:"
    )
    bot_manager.password_msg_id = password_msg.message_id
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الحصول على كلمة المرور"""
    user_id = update.effective_user.id
    bot_manager = get_bot_manager(user_id)
    
    if not bot_manager.username:
        await update.message.reply_text("❌ لم يتم حفظ الإيميل. يرجى البدء من جديد")
        return ConversationHandler.END
    
    password = update.message.text
    bot_manager.password = password
    
    # حذف رسالة طلب كلمة المرور
    try:
        await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.password_msg_id)
    except Exception as e:
        logger.error(f"خطأ في حذف رسالة طلب كلمة المرور للمستخدم {user_id}: {e}")
    
    # التحقق من أن المتصفح جاهز
    if not bot_manager.is_browser_ready:
        await update.message.reply_text("❌ المتصفح غير جاهز. يرجى إعادة تشغيل البوت")
        return ConversationHandler.END
    
    # إرسال رسالة بدء عملية تسجيل الدخول
    login_process_msg = await update.message.reply_text(
        text="🔐 جاري محاولة تسجيل الدخول...\n\n1. جاري البحث عن حقل الإيميل\n2. جاري إدخال الإيميل\n3. جاري البحث عن حقل كلمة المرور\n4. جاري إدخال كلمة المرور\n5. جاري النقر على زر تسجيل الدخول\n6. جاري التحقق من نجاح التسجيل"
    )
    bot_manager.login_process_msg_id = login_process_msg.message_id
    
    # محاولة تسجيل الدخول
    result = await perform_login(
        bot_manager.username, 
        password, 
        user_id
    )
    
    # حذف رسالة عملية تسجيل الدخول
    try:
        await context.bot.delete_message(chat_id=user_id, message_id=bot_manager.login_process_msg_id)
    except Exception as e:
        logger.error(f"خطأ في حذف رسالة عملية التسجيل للمستخدم {user_id}: {e}")
    
    if result['success']:
        # جلب بيانات المستخدمين
        await refresh_user_data(user_id)
        
        # إرسال رسالة النجاح مع الأزرار
        keyboard = create_main_keyboard(bot_manager)
        await update.message.reply_text(
            text="✅ تم تسجيل الدخول بنجاح!",
            reply_markup=keyboard
        )
    else:
        # إرسال رسالة الفشل
        error_msg = result.get('message', 'فشل تسجيل الدخول')
        keyboard = [[InlineKeyboardButton("🔄 حاول مرة أخرى", callback_data="start_pressed")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=f"❌ فشل تسجيل الدخول: {error_msg}",
            reply_markup=reply_markup
        )
    
    return ConversationHandler.END

# ====== دوال تسجيل الدخول ======
async def perform_login(username, password, user_id):
    """أداء عملية تسجيل الدخول مع تحسين الأداء"""
    bot_manager = get_bot_manager(user_id)
    
    if not bot_manager.is_browser_ready or not bot_manager.driver:
        return {'success': False, 'message': 'المتصفح غير جاهز'}
    
    try:
        # استخدام partial لتمرير المعلمات مع الدالة
        login_task = partial(_perform_login_sync, bot_manager, username, password)
        
        # تشغيل المهمة في الـ executor
        result = await asyncio.get_event_loop().run_in_executor(executor, login_task)
        return result
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في عملية التسجيل للمستخدم {user_id}: {e}")
        return {'success': False, 'message': f'خطأ تقني: {str(e)}'}

def _perform_login_sync(bot_manager, username, password):
    """النسخة المتزامنة من عملية تسجيل الدخول لتشغيلها في thread منفصل"""
    try:
        driver = bot_manager.driver
        
        # الانتقال إلى صفحة التسجيل
        driver.get("https://merchant.totersapp.com/#/")
        
        # انتظار تحميل الصفحة بشكل كامل
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # انتظار إضافي لضمان تحميل جميع العناصر
        
        # البحث عن حقل الإيميل بطرق متعددة
        email_field = None
        try:
            # الطريقة الأولى: البحث بالـ XPATH
            email_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email' or @ng-model='vm.user.email']"))
            )
            logger.info(f"✅ تم العثور على حقل الإيميل بالطريقة الأولى للمستخدم {bot_manager.user_id}")
        except:
            try:
                # الطريقة الثانية: البحث بالـ CSS Selector
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                )
                logger.info(f"✅ تم العثور على حقل الإيميل بالطريقة الثانية للمستخدم {bot_manager.user_id}")
            except:
                try:
                    # الطريقة الثالثة: البحث بالـ Name
                    email_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "email"))
                    )
                    logger.info(f"✅ تم العثور على حقل الإيميل بالطريقة الثالثة للمستخدم {bot_manager.user_id}")
                except:
                    try:
                        # الطريقة الرابعة: البحث بالـ ID
                        email_field = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "email"))
                        )
                        logger.info(f"✅ تم العثور على حقل الإيميل بالطريقة الرابعة للمستخدم {bot_manager.user_id}")
                    except:
                        pass
        
        if not email_field:
            logger.error(f"❌ تعذر العثور على حقل الإيميل للمستخدم {bot_manager.user_id}")
            return {'success': False, 'message': 'تعذر العثور على حقل الإيميل'}
        
        # التأكد من أن حقل الإيميل مرئي وقابل للتفاعل
        WebDriverWait(driver, 10).until(
            EC.visibility_of(email_field)
        )
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(email_field)
        )
        
        # مسح حقل الإيميل وإدخال البريد الإلكتروني
        email_field.clear()
        email_field.click()
        email_field.send_keys(username)
        logger.info(f"✅ تم إدخال الإيميل للمستخدم {bot_manager.user_id}")
        
        # انتظار قصير قبل البحث عن حقل كلمة المرور
        time.sleep(1)
        
        # البحث عن حقل كلمة المرور بطرق متعددة
        password_field = None
        try:
            # الطريقة الأولى: البحث بالـ XPATH
            password_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='password' or @ng-model='vm.user.password']"))
            )
            logger.info(f"✅ تم العثور على حقل كلمة المرور بالطريقة الأولى للمستخدم {bot_manager.user_id}")
        except:
            try:
                # الطريقة الثانية: البحث بالـ CSS Selector
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                logger.info(f"✅ تم العثور على حقل كلمة المرور بالطريقة الثانية للمستخدم {bot_manager.user_id}")
            except:
                try:
                    # الطريقة الثالثة: البحث بالـ Name
                    password_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "password"))
                    )
                    logger.info(f"✅ تم العثور على حقل كلمة المرور بالطريقة الثالثة للمستخدم {bot_manager.user_id}")
                except:
                    try:
                        # الطريقة الرابعة: البحث بالـ ID
                        password_field = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "password"))
                        )
                        logger.info(f"✅ تم العثور على حقل كلمة المرور بالطريقة الرابعة للمستخدم {bot_manager.user_id}")
                    except:
                        pass
        
        if not password_field:
            logger.error(f"❌ تعذر العثور على حقل كلمة المرور للمستخدم {bot_manager.user_id}")
            return {'success': False, 'message': 'تعذر العثور على حقل كلمة المرور'}
        
        # التأكد من أن حقل كلمة المرور مرئي وقابل للتفاعل
        WebDriverWait(driver, 10).until(
            EC.visibility_of(password_field)
        )
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(password_field)
        )
        
        # مسح حقل كلمة المرور وإدخال كلمة المرور
        password_field.clear()
        password_field.click()
        password_field.send_keys(password)
        logger.info(f"✅ تم إدخال كلمة المرور للمستخدم {bot_manager.user_id}")
        
        # انتظار قصير قبل البحث عن زر تسجيل الدخول
        time.sleep(1)
        
        # البحث عن زر تسجيل الدخول بطرق متعددة
        login_button = None
        try:
            # الطريقة الأولى: البحث بالـ XPATH
            login_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            logger.info(f"✅ تم العثور على زر تسجيل الدخول بالطريقة الأولى للمستخدم {bot_manager.user_id}")
        except:
            try:
                # الطريقة الثانية: البحث بالـ CSS Selector
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                )
                logger.info(f"✅ تم العثور على زر تسجيل الدخول بالطريقة الثانية للمستخدم {bot_manager.user_id}")
            except:
                try:
                    # الطريقة الثالثة: البحث عن نص Login أو Sign In
                    login_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign In')]"))
                    )
                    logger.info(f"✅ تم العثور على زر تسجيل الدخول بالطريقة الثالثة للمستخدم {bot_manager.user_id}")
                except:
                    try:
                        # الطريقة الرابعة: البحث بالـ ID
                        login_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "login-button"))
                        )
                        logger.info(f"✅ تم العثور على زر تسجيل الدخول بالطريقة الرابعة للمستخدم {bot_manager.user_id}")
                    except:
                        try:
                            # الطريقة الخامسة: البحث بالـ Class
                            login_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "login-button"))
                            )
                            logger.info(f"✅ تم العثور على زر تسجيل الدخول بالطريقة الخامسة للمستخدم {bot_manager.user_id}")
                        except:
                            pass
        
        if not login_button:
            logger.error(f"❌ تعذر العثور على زر التسجيل للمستخدم {bot_manager.user_id}")
            return {'success': False, 'message': 'تعذر العثور على زر التسجيل'}
        
        # التأكد من أن زر تسجيل الدخول مرئي وقابل للنقر
        WebDriverWait(driver, 10).until(
            EC.visibility_of(login_button)
        )
        
        # النقر على زر تسجيل الدخول
        login_button.click()
        logger.info(f"✅ تم النقر على زر تسجيل الدخول للمستخدم {bot_manager.user_id}")
        
        # الانتظار للتحقق من نجاح التسجيل
        time.sleep(5)
        
        # التحقق من وجود عناصر تدل على نجاح التسجيل بطرق متعددة
        success = False
        
        # الطريقة الأولى: البحث عن نص Online أو Offline
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Online') or contains(text(), 'Offline')]"))
            )
            success = True
            logger.info(f"✅ تم التحقق من تسجيل الدخول بالطريقة الأولى للمستخدم {bot_manager.user_id}")
        except:
            pass
        
        # الطريقة الثانية: البحث عن عنصر لوحة التحكم
        if not success:
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'dashboard') or contains(@class, 'main')]"))
                )
                success = True
                logger.info(f"✅ تم التحقق من تسجيل الدخول بالطريقة الثانية للمستخدم {bot_manager.user_id}")
            except:
                pass
        
        # الطريقة الثالثة: التحقق من تغيير URL
        if not success:
            try:
                current_url = driver.current_url
                if "dashboard" in current_url or "home" in current_url or "main" in current_url:
                    success = True
                    logger.info(f"✅ تم التحقق من تسجيل الدخول بالطريقة الثالثة للمستخدم {bot_manager.user_id}")
            except:
                pass
        
        # الطريقة الرابعة: البحث عن رسالة ترحيب
        if not success:
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Welcome') or contains(text(), 'مرحبا')]"))
                )
                success = True
                logger.info(f"✅ تم التحقق من تسجيل الدخول بالطريقة الرابعة للمستخدم {bot_manager.user_id}")
            except:
                pass
        
        if success:
            logger.info(f"✅ تم تسجيل الدخول بنجاح للمستخدم {bot_manager.user_id}")
            return {'success': True}
        else:
            logger.error(f"❌ فشل التحقق من تسجيل الدخول للمستخدم {bot_manager.user_id}")
            return {'success': False, 'message': 'فشل التحقق من تسجيل الدخول'}
            
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع في عملية التسجيل المتزامنة للمستخدم {bot_manager.user_id}: {e}")
        return {'success': False, 'message': str(e)}
    finally:
        # تأكد من أن المتصفح لا يزال في حالة جيدة
        if bot_manager.driver:
            try:
                # تحقق من أن الصفحة لا تزال محملة
                _ = bot_manager.driver.current_url
            except:
                logger.warning(f"⚠️ المتصفح في حالة غير مستقرة للمستخدم {bot_manager.user_id}")
                try:
                    bot_manager.close_browser()
                    bot_manager.init_browser()
                except Exception as e:
                    logger.error(f"❌ فشل في إعادة تهيئة المتصفح للمستخدم {bot_manager.user_id}: {e}")

# ====== دوال تحديث البيانات ======
async def refresh_page_safely(driver, user_id):
    """تحديث الصفحة بشكل آمن مع معالجة الأخطاء"""
    try:
        logger.info(f"🔄 جاري تحديث الصفحة للمستخدم {user_id}")
        driver.refresh()
        
        # انتظار تحميل الصفحة
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # انتظار إضافي لضمان تحميل جميع العناصر الديناميكية
        time.sleep(3)
        
        logger.info(f"✅ تم تحديث الصفحة بنجاح للمستخدم {user_id}")
        return True
    except TimeoutException:
        logger.error(f"❌ انتهت مهلة تحميل الصفحة للمستخدم {user_id}")
        return False
    except WebDriverException as e:
        logger.error(f"❌ خطأ في المتصفح أثناء تحديث الصفحة للمستخدم {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع أثناء تحديث الصفحة للمستخدم {user_id}: {e}")
        return False

async def refresh_user_data(user_id):
    """تحديث بيانات المستخدمين مع تحديث البيانات المخزنة فقط"""
    try:
        bot_manager = get_bot_manager(user_id)
        
        if not bot_manager.is_browser_ready or not bot_manager.driver:
            return False
        
        driver = bot_manager.driver
        
        # تحديث الصفحة أولاً
        try:
            logger.info(f"🔄 جاري تحديث الصفحة للمستخدم {user_id}")
            driver.refresh()
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # انتظار إضافي لضمان تحميل جميع العناصر
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الصفحة للمستخدم {user_id}: {e}")
            return False
        
        # محاولة جلب البيانات مع إعادة المحاولة
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # جلب عدد المستخدمين المتصلين وغير المتصلين مع تحديث البيانات المخزنة
                success_online = await fetch_online_users(user_id)
                success_offline = await fetch_offline_users(user_id)
                
                if success_online and success_offline:
                    return True
                else:
                    logger.warning(f"⚠️ محاولة {attempt + 1} فشلت في جلب البيانات للمستخدم {user_id}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # انتظار قبل إعادة المحاولة
                        driver.refresh()  # تحديث الصفحة مرة أخرى
                        WebDriverWait(driver, 30).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        time.sleep(2)
            except Exception as e:
                logger.error(f"❌ خطأ في محاولة {attempt + 1} لجلب البيانات للمستخدم {user_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        logger.error(f"❌ فشلت جميع محاولات تحديث البيانات للمستخدم {user_id}")
        return False
    except Exception as e:
        logger.error(f"❌ خطأ في تحديث بيانات المستخدمين للمستخدم {user_id}: {e}")
        return False

async def fetch_online_users(user_id):
    """جلب قائمة المستخدمين المتصلين مع تخزين البيانات الكاملة"""
    try:
        bot_manager = get_bot_manager(user_id)
        
        if not bot_manager.is_browser_ready or not bot_manager.driver:
            return False
        
        driver = bot_manager.driver
        
        # البحث عن عنصر Online والنقر عليه
        online_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Online')]")
        if online_elements:
            try:
                # الانتظار حتى يصبح العنصر قابلاً للنقر
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Online')]"))
                )
                
                # استخدام JavaScript للنقر (يتجاوز العناصر المعترضة)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", online_elements[0])
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", online_elements[0])
                
                # الانتظار حتى تظهر قائمة المستخدمين
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//h3[contains(@class, 'ng-binding')]"))
                )
                
                # انتظار إضافي لضمان تحميل جميع العناصر
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ خطأ في النقر على عنصر Online للمستخدم {user_id}: {e}")
                return False
        
        # جلب عناصر المستخدمين المتصلين
        user_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'dot-50')]/ancestor::div[contains(@class, 'md-list-item-text')]")
        
        # قائمة مؤقتة للمستخدمين المتصلين الجدد
        temp_online_users = []
        
        for element in user_elements:
            try:
                # استخراج اسم المستخدم
                name_element = element.find_element(By.XPATH, ".//h3[contains(@class, 'ng-binding')]")
                name = name_element.text.strip()
                
                # التحقق من أن المستخدم ليس في قائمة منتهي الصلاحية
                is_expired = False
                for expired_user in bot_manager.expired_users:
                    if expired_user.get('name') == name:
                        is_expired = True
                        break
                
                if is_expired:
                    continue  # تخطي المستخدم إذا كان منتهي الصلاحية
                
                # استخراج الاسم الكامل (بدون كلمة free)
                full_name = re.sub(r'\s*free\s*$', '', name, flags=re.IGNORECASE).strip()
                
                # استخراج رقم الهاتف
                try:
                    phone_element = element.find_element(By.XPATH, ".//a[contains(@href, 'tel:')]")
                    phone = phone_element.text.strip()
                except:
                    phone = 'غير متوفر'
                
                # استخراج تاريخ آخر طلب
                try:
                    last_order_element = element.find_element(By.XPATH, ".//p[contains(text(), 'Last order delivered')]")
                    last_order = last_order_element.text.replace('Last order delivered: ', '').strip()
                except:
                    last_order = 'غير متوفر'
                
                # استخراج عدد الطلبات
                try:
                    order_count_element = element.find_element(By.XPATH, ".//p[contains(text(), 'Orders delivered today')]")
                    order_count = order_count_element.text.replace('Orders delivered today: ', '').strip()
                except:
                    order_count = 'غير متوفر'
                
                # استخراج محفظة الكابتن
                try:
                    wallet_element = element.find_element(By.XPATH, ".//p[contains(text(), 'Payments wallet')]")
                    wallet = wallet_element.text.replace('Payments wallet: ', '').strip()
                except:
                    wallet = 'غير متوفر'
                
                if name:  # التأكد من أن الاسم ليس فارغًا
                    temp_online_users.append({
                        'name': name,
                        'full_name': full_name,
                        'phone': phone,
                        'last_order': last_order,
                        'order_count': order_count,
                        'captain_wallet': wallet
                    })
            except Exception as e:
                logger.error(f"خطأ في استخراج بيانات مستخدم متصل: {e}")
        
        # تحديث قائمة المستخدمين المتصلين
        bot_manager.online_users = temp_online_users
        
        # الحصول على العدد من النص إذا أمكن
        if online_elements:
            online_text = online_elements[0].text
            numbers = re.findall(r'\((\d+)\)', online_text)
            if numbers:
                bot_manager.online_count = int(numbers[0])
            else:
                bot_manager.online_count = len(bot_manager.online_users)
        else:
            bot_manager.online_count = len(bot_manager.online_users)
        
        # التحقق من صحة البيانات
        if bot_manager.online_count == 0 and len(bot_manager.online_users) == 0:
            logger.warning(f"لم يتم العثور على مستخدمين متصلين للمستخدم {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"خطأ في جلب المستخدمين المتصلين للمستخدم {user_id}: {e}")
        return False

async def fetch_offline_users(user_id):
    """جلب قائمة المستخدمين غير المتصلين مع تخزين البيانات الكاملة"""
    try:
        bot_manager = get_bot_manager(user_id)
        
        if not bot_manager.is_browser_ready or not bot_manager.driver:
            return False
        
        driver = bot_manager.driver
        
        # البحث عن عنصر Offline والنقر عليه
        offline_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Offline')]")
        if offline_elements:
            try:
                # الانتظار حتى يصبح العنصر قابلاً للنقر
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Offline')]"))
                )
                
                # استخدام JavaScript للنقر (يتجاوز العناصر المعترضة)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", offline_elements[0])
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", offline_elements[0])
                
                # الانتظار حتى تظهر قائمة المستخدمين
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//h3[contains(@class, 'ng-binding')]"))
                )
                
                # انتظار إضافي لضمان تحميل جميع العناصر
                time.sleep(2)
            except Exception as e:
                logger.error(f"❌ خطأ في النقر على عنصر Offline للمستخدم {user_id}: {e}")
                return False
        
        # جلب عناصر المستخدمين غير المتصلين
        user_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'dot-40')]/ancestor::div[contains(@class, 'md-list-item-text')]")
        
        # قائمة مؤقتة للمستخدمين غير المتصلين الجدد
        temp_offline_users = []
        
        for element in user_elements:
            try:
                # استخراج اسم المستخدم
                name_element = element.find_element(By.XPATH, ".//h3[contains(@class, 'ng-binding')]")
                name = name_element.text.strip()
                
                # التحقق من أن المستخدم ليس في قائمة منتهي الصلاحية
                is_expired = False
                for expired_user in bot_manager.expired_users:
                    if expired_user.get('name') == name:
                        is_expired = True
                        break
                
                if is_expired:
                    continue  # تخطي المستخدم إذا كان منتهي الصلاحية
                
                # استخراج الاسم الكامل (بدون كلمة free)
                full_name = re.sub(r'\s*free\s*$', '', name, flags=re.IGNORECASE).strip()
                
                # استخراج رقم الهاتف
                try:
                    phone_element = element.find_element(By.XPATH, ".//a[contains(@href, 'tel:')]")
                    phone = phone_element.text.strip()
                except:
                    phone = 'غير متوفر'
                
                # استخراج تاريخ آخر طلب
                try:
                    last_order_element = element.find_element(By.XPATH, ".//p[contains(text(), 'Last order delivered')]")
                    last_order = last_order_element.text.replace('Last order delivered: ', '').strip()
                except:
                    last_order = 'غير متوفر'
                
                # استخراج عدد الطلبات
                try:
                    order_count_element = element.find_element(By.XPATH, ".//p[contains(text(), 'Orders delivered today')]")
                    order_count = order_count_element.text.replace('Orders delivered today: ', '').strip()
                except:
                    order_count = 'غير متوفر'
                
                # استخراج محفظة الكابتن
                try:
                    wallet_element = element.find_element(By.XPATH, ".//p[contains(text(), 'Payments wallet')]")
                    wallet = wallet_element.text.replace('Payments wallet: ', '').strip()
                except:
                    wallet = 'غير متوفر'
                
                if name:  # التأكد من أن الاسم ليس فارغًا
                    temp_offline_users.append({
                        'name': name,
                        'full_name': full_name,
                        'phone': phone,
                        'last_order': last_order,
                        'order_count': order_count,
                        'captain_wallet': wallet
                    })
            except Exception as e:
                logger.error(f"خطأ في استخراج بيانات مستخدم غير متصل: {e}")
        
        # تحديث قائمة المستخدمين غير المتصلين
        bot_manager.offline_users = temp_offline_users
        
        # الحصول على العدد من النص إذا أمكن
        if offline_elements:
            offline_text = offline_elements[0].text
            numbers = re.findall(r'\((\d+)\)', offline_text)
            if numbers:
                bot_manager.offline_count = int(numbers[0])
            else:
                bot_manager.offline_count = len(bot_manager.offline_users)
        else:
            bot_manager.offline_count = len(bot_manager.offline_users)
        
        # التحقق من صحة البيانات
        if bot_manager.offline_count == 0 and len(bot_manager.offline_users) == 0:
            logger.warning(f"لم يتم العثور على مستخدمين غير متصلين للمستخدم {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"خطأ في جلب المستخدمين غير المتصلين للمستخدم {user_id}: {e}")
        return False

async def get_user_info_optimized(index, user_type, user_id):
    """الحصول على معلومات مستخدم معين من البيانات المخزنة"""
    try:
        bot_manager = get_bot_manager(user_id)
        
        # تحديد نوع المستخدم (متصل/غير متصل/منتهي الصلاحية)
        if user_type == True or user_type == "online":
            users = bot_manager.online_users
            status_text = "Online"
        elif user_type == False or user_type == "offline":
            users = bot_manager.offline_users
            status_text = "Offline"
        elif user_type == "expired":
            users = bot_manager.expired_users
            status_text = "منتهي الصلاحية"
        else:
            return None
        
        # التأكد من أن الفهرس صحيح
        if index < 0 or index >= len(users):
            return None
        
        # استرجاع معلومات المستخدم من البيانات المخزنة
        user_info = users[index].copy()
        user_info['details'] = f'مستخدم {status_text} - تم الجلب في {datetime.now().strftime("%H:%M:%S")}'
        
        return user_info
        
    except Exception as e:
        logger.error(f"خطأ في جلب معلومات المستخدم للمستخدم {user_id}: {e}")
        return None

# ====== دوال التنظيف والجدولة ======
def start_cleanup_scheduler():
    """بدء مجدول تنظيف الجلسات غير النشطة"""
    def cleanup_sessions():
        with session_lock:
            current_time = time.time()
            expired_users = []
            
            for user_id, bot_manager in users_data.items():
                if current_time - bot_manager.last_activity > SESSION_TIMEOUT:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                try:
                    bot_manager = users_data[user_id]
                    bot_manager.close_browser()
                    bot_manager.reset_state()
                    del users_data[user_id]
                    logger.info(f"✅ تم تنظيف جلسة المستخدم {user_id} بسبب عدم النشاط")
                except Exception as e:
                    logger.error(f"❌ خطأ في تنظيف جلسة المستخدم {user_id}: {e}")
    
    # تشغيل المجدول كل 5 دقائق
    import threading
    def scheduler():
        while True:
            time.sleep(300)  # 5 دقائق
            cleanup_sessions()
    
    scheduler_thread = threading.Thread(target=scheduler, daemon=True)
    scheduler_thread.start()

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
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)
    
    # إضافة معالج الأزرار
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # إضافة دالة البدء
    application.job_queue.run_once(lambda context: on_start(application), when=0)
    
    # بدء البوت
    logger.info("🚀 جاري بدء تشغيل البوت...")
    application.run_polling()

if __name__ == "__main__":
    main()

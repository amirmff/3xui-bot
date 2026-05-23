"""Persian language strings for the 3x-ui Telegram bot."""

# ─── Main Menu ────────────────────────────────────────────────────────────────

WELCOME = (
    "🌐 <b>مدیریت پنل 3x-ui</b>\n\n"
    "سلام! از منوی زیر برای مدیریت پنل VPN استفاده کنید.\n\n"
    "⚡ <i>قدرت‌گرفته از Xray-core</i>"
)

HELP = (
    "ℹ️ <b>راهنما — امکانات ربات</b>\n\n"
    "📋 <b>اینباندها</b>\n"
    "  • لیست، افزودن، ویرایش، حذف اینباند\n"
    "  • فعال/غیرفعال کردن\n"
    "  • مشاهده جزئیات و ترافیک\n\n"
    "👥 <b>کاربران</b>\n"
    "  • مشاهده کاربران هر اینباند\n"
    "  • افزودن، ویرایش، حذف کاربر\n"
    "  • مشاهده ترافیک و اطلاعات اتصال\n"
    "  • ساخت لینک اتصال و QR Code\n"
    "  • ریست ترافیک، مدیریت IP\n"
    "  • جستجوی کاربر با ایمیل\n"
    "  • افزودن روز/حجم به کاربر\n"
    "  • عملیات‌های گروهی\n\n"
    "🖥 <b>سرور</b>\n"
    "  • وضعیت لحظه‌ای (CPU/RAM/Disk)\n"
    "  • ریستارت / توقف Xray\n"
    "  • نصب / آپدیت نسخه Xray\n"
    "  • آپدیت فایل‌های GeoIP/GeoSite\n"
    "  • مشاهده لاگ‌های سیستم و Xray\n"
    "  • تولید UUID و کلید X25519\n\n"
    "💾 <b>بکاپ</b>\n"
    "  • دانلود بکاپ دیتابیس\n"
    "  • دانلود کانفیگ Xray\n"
    "  • ایمپورت دیتابیس\n"
    "  • ارسال بکاپ به تلگرام\n\n"
    "📡 <b>کاربران آنلاین</b>\n"
    "  • مشاهده کاربران متصل\n\n"
    "⏰ <b>مانیتورینگ خودکار</b>\n"
    "  • بررسی ترافیک کاربران هر ۵ دقیقه\n"
    "  • ریستارت خودکار Xray در صورت مصرف بیش از حد\n"
    "  • هشدار انقضای کاربران\n\n"
    "<b>دستورات:</b>\n"
    "  /start — منوی اصلی\n"
    "  /help — راهنما\n"
    "  /cancel — لغو عملیات جاری\n"
    "  /status — وضعیت سرور"
)

# ─── Buttons ──────────────────────────────────────────────────────────────────

BTN_INBOUNDS = "📋 اینباندها"
BTN_CLIENTS = "👥 کاربران"
BTN_SERVER = "🖥 سرور"
BTN_BACKUP = "💾 بکاپ"
BTN_ONLINE = "📡 آنلاین‌ها"
BTN_HELP = "ℹ️ راهنما"
BTN_STATUS = "📊 وضعیت"
BTN_PANELS = "🖥 پنل‌ها"
BTN_BACK = "⬅️ بازگشت"
BTN_CONFIRM_YES = "✅ بله"
BTN_CONFIRM_NO = "❌ خیر"
BTN_CANCEL = "❌ لغو"
BTN_REFRESH = "🔄 بروزرسانی"

# ─── Inbound Strings ─────────────────────────────────────────────────────────

INB_MANAGEMENT = "📋 <b>مدیریت اینباندها</b>\n\nعملیات مورد نظر را انتخاب کنید:"
INB_LIST_TITLE = "📋 <b>اینباندها ({count})</b>\n\nیک اینباند انتخاب کنید:"
INB_LIST_EMPTY = "📋 <b>اینباندها</b>\n\nهیچ اینباندی یافت نشد."
INB_LIST_ALL = "📋 لیست اینباندها"
INB_ADD = "➕ افزودن اینباند"
INB_ADD_TITLE = "➕ <b>افزودن اینباند جدید</b>"
INB_ADD_PROTOCOL = "مرحله ۱/۵: پروتکل را انتخاب کنید:"
INB_ADD_REMARK = "مرحله ۲/۵: یک <b>نام</b> برای اینباند وارد کنید:"
INB_ADD_PORT = "مرحله ۳/۵: <b>شماره پورت</b> (1-65535) وارد کنید:"
INB_ADD_NETWORK = "مرحله ۴/۵: نوع <b>شبکه</b> را انتخاب کنید:"
INB_ADD_SECURITY = "مرحله ۵/۵: <b>امنیت</b> را انتخاب کنید:"
INB_ADD_CONFIRM = "➕ <b>تأیید اینباند جدید</b>"
INB_ADD_SUCCESS = "✅ <b>اینباند با موفقیت ایجاد شد!</b>"
INB_ADD_CANCEL = "❌ ایجاد اینباند لغو شد."
INB_DELETE_CONFIRM = "⚠️ <b>حذف اینباند #{id}؟</b>\n\nاین عملیات اینباند و <b>تمام کاربران</b> آن را حذف می‌کند.\nاین عمل قابل بازگشت نیست!"
INB_DELETE_SUCCESS = "✅ اینباند با موفقیت حذف شد."
INB_TOGGLE_ENABLED = "✅ اینباند <b>{remark}</b> فعال شد."
INB_TOGGLE_DISABLED = "❌ اینباند <b>{remark}</b> غیرفعال شد."
INB_VIEW_CLIENTS = "👥 مشاهده کاربران"

# ─── Client Strings ───────────────────────────────────────────────────────────

CL_MANAGEMENT = "👥 <b>مدیریت کاربران</b>\n\nعملیات مورد نظر را انتخاب کنید:"
CL_SELECT_INBOUND = "👥 <b>انتخاب اینباند</b>\n\nاینباند مورد نظر را انتخاب کنید:"
CL_LIST_TITLE = "👥 <b>کاربران: {remark}</b> ({count} نفر)\n\nیک کاربر انتخاب کنید:"
CL_LIST_EMPTY = "👥 <b>کاربران: {remark}</b>\n\nهیچ کاربری یافت نشد."
CL_BROWSE = "📋 مشاهده بر اساس اینباند"
CL_ADD = "➕ افزودن کاربر"
CL_SEARCH = "🔍 جستجو با ایمیل"
CL_SEARCH_TITLE = "🔍 <b>جستجوی کاربر</b>\n\n<b>ایمیل</b> کاربر را وارد کنید:\n\nبرای لغو /cancel بزنید."
CL_SEARCH_NOT_FOUND = "❌ کاربر <code>{email}</code> یافت نشد."
CL_ADD_SELECT_INB = "➕ <b>افزودن کاربر</b>\n\nمرحله ۱/۵: اینباند را انتخاب کنید:"
CL_ADD_EMAIL = "مرحله ۲/۵: <b>ایمیل/نام کاربری</b> وارد کنید:"
CL_ADD_TRAFFIC = "مرحله ۳/۵: <b>حجم ترافیک (GB)</b> وارد کنید (0 = نامحدود):"
CL_ADD_EXPIRY = "مرحله ۴/۵: <b>مدت زمان (روز)</b> وارد کنید (0 = بدون انقضا):"
CL_ADD_IP_LIMIT = "مرحله ۵/۵: <b>محدودیت IP</b> وارد کنید (0 = نامحدود):"
CL_ADD_CONFIRM = "➕ <b>تأیید کاربر جدید</b>"
CL_ADD_SUCCESS = "✅ <b>کاربر با موفقیت ایجاد شد!</b>"
CL_ADD_CANCEL = "❌ ایجاد کاربر لغو شد."
CL_DELETE_CONFIRM = "🗑 <b>حذف کاربر <code>{email}</code>؟</b>\n\nاین عمل قابل بازگشت نیست!"
CL_DELETE_SUCCESS = "✅ کاربر <code>{email}</code> حذف شد."
CL_TOGGLE_ENABLED = "✅ کاربر <code>{email}</code> فعال شد."
CL_TOGGLE_DISABLED = "❌ کاربر <code>{email}</code> غیرفعال شد."
CL_RESET_TRAFFIC_CONFIRM = "🔄 <b>ریست ترافیک <code>{email}</code>؟</b>"
CL_RESET_TRAFFIC_SUCCESS = "✅ ترافیک <code>{email}</code> ریست شد."
CL_IPS_TITLE = "🌐 <b>آی‌پی‌های کاربر: {email}</b>"
CL_IPS_EMPTY = "🌐 <b>آی‌پی‌های کاربر: {email}</b>\n\nهیچ رکوردی یافت نشد."
CL_IPS_CLEARED = "✅ رکورد آی‌پی <code>{email}</code> پاک شد."
CL_LINK_TITLE = "🔗 <b>لینک اتصال</b>"
CL_NOT_FOUND = "❌ کاربر <code>{email}</code> یافت نشد."

# ─── NEW: Add Days / Traffic / Renew ──────────────────────────────────────────

CL_ADD_DAYS = "➕ افزودن روز"
CL_ADD_TRAFFIC_VOL = "➕ افزودن حجم"
CL_RENEW = "🔄 تمدید"
CL_ADD_DAYS_PROMPT = "➕ <b>افزودن روز به {email}</b>\n\nتعداد <b>روز</b> را وارد کنید:"
CL_ADD_DAYS_SUCCESS = "✅ <b>{days} روز</b> به کاربر <code>{email}</code> اضافه شد.\n\nانقضای جدید: {new_expiry}"
CL_ADD_TRAFFIC_PROMPT = "➕ <b>افزودن حجم به {email}</b>\n\nمقدار حجم <b>(GB)</b> را وارد کنید:"
CL_ADD_TRAFFIC_SUCCESS = "✅ <b>{gb} گیگابایت</b> به کاربر <code>{email}</code> اضافه شد.\n\nحجم جدید: {new_total}"
CL_RENEW_PROMPT = (
    "🔄 <b>تمدید کاربر {email}</b>\n\n"
    "حجم جدید <b>(GB)</b> و مدت <b>(روز)</b> را وارد کنید.\n"
    "فرمت: <code>حجم روز</code>\n"
    "مثال: <code>50 30</code> (۵۰ گیگ، ۳۰ روز)"
)
CL_RENEW_SUCCESS = "✅ کاربر <code>{email}</code> تمدید شد.\n\nحجم: {gb} GB | مدت: {days} روز"

# ─── Bulk Operations ──────────────────────────────────────────────────────────

BULK_RESET_ALL = "🔄 ریست همه ترافیک‌ها"
BULK_RESET_ALL_CONFIRM = "⚠️ <b>ریست ترافیک همه کاربران در همه اینباندها؟</b>"
BULK_RESET_ALL_SUCCESS = "✅ ترافیک همه کاربران ریست شد!"
BULK_RESET_INB = "🔄 ریست ترافیک اینباند"
BULK_DEL_DEPLETED = "🗑 حذف تمام‌شده‌ها"
BULK_ADD_DAYS_ALL = "➕ افزودن روز به همه"
BULK_ADD_TRAFFIC_ALL = "➕ افزودن حجم به همه"
BULK_ADD_DAYS_PROMPT = "➕ <b>افزودن روز به همه کاربران</b>\n\nتعداد <b>روز</b> را وارد کنید:"
BULK_ADD_DAYS_SUCCESS = "✅ <b>{days} روز</b> به {count} کاربر اضافه شد."
BULK_ADD_TRAFFIC_PROMPT = "➕ <b>افزودن حجم به همه کاربران</b>\n\nمقدار حجم <b>(GB)</b> را وارد کنید:"
BULK_ADD_TRAFFIC_SUCCESS = "✅ <b>{gb} گیگابایت</b> به {count} کاربر اضافه شد."

# ─── Quick Templates ──────────────────────────────────────────────────────────

QUICK_TEMPLATES = "⚡ ساخت سریع کاربر"
QUICK_TEMPLATE_LIST = (
    "⚡ <b>ساخت سریع</b>\n\nیک قالب انتخاب کنید:"
)
TEMPLATES = [
    {"label": "🟢 ۱ ماهه ۵۰ گیگ", "days": 30, "gb": 50, "ip": 2},
    {"label": "🔵 ۱ ماهه ۱۰۰ گیگ", "days": 30, "gb": 100, "ip": 3},
    {"label": "🟡 ۳ ماهه ۱۵۰ گیگ", "days": 90, "gb": 150, "ip": 2},
    {"label": "🟣 ۶ ماهه ۳۰۰ گیگ", "days": 180, "gb": 300, "ip": 3},
    {"label": "🔴 نامحدود ۱ ماهه", "days": 30, "gb": 0, "ip": 2},
]

# ─── Server Strings ───────────────────────────────────────────────────────────

SRV_MANAGEMENT = "🖥 <b>مدیریت سرور</b>\n\nعملیات مورد نظر را انتخاب کنید:"
SRV_STATUS = "📊 وضعیت"
SRV_RESTART_XRAY = "🔄 ریستارت Xray"
SRV_STOP_XRAY = "⏹ توقف Xray"
SRV_XRAY_VER = "📋 نسخه Xray"
SRV_UPDATE_GEO = "🌍 آپدیت GeoFiles"
SRV_SYS_LOGS = "📜 لاگ سیستم"
SRV_XRAY_LOGS = "📜 لاگ Xray"
SRV_NEW_UUID = "🔑 UUID جدید"
SRV_NEW_X25519 = "🔑 کلید X25519"
SRV_RESTART_CONFIRM = "🔄 <b>ریستارت سرویس Xray؟</b>\n\nاتصال کاربران موقتاً قطع خواهد شد."
SRV_RESTART_SUCCESS = "✅ سرویس Xray با موفقیت ریستارت شد!"
SRV_STOP_CONFIRM = "⚠️ <b>توقف سرویس Xray؟</b>\n\nاتصال <b>همه</b> کاربران فوراً قطع خواهد شد!"
SRV_STOP_SUCCESS = "✅ سرویس Xray متوقف شد."
SRV_GEO_SUCCESS = "✅ فایل‌های GeoIP/GeoSite با موفقیت آپدیت شدند!"
SRV_UUID_TITLE = "🔑 <b>UUID جدید</b>"
SRV_UUID_ANOTHER = "🔑 تولید دوباره"
SRV_X25519_TITLE = "🔑 <b>گواهی X25519 جدید</b>"
SRV_INSTALL_CONFIRM = "📥 <b>نصب Xray {version}؟</b>\n\nسرویس Xray ریستارت خواهد شد."
SRV_INSTALL_SUCCESS = "✅ Xray {version} با موفقیت نصب شد!"
SRV_VERSIONS_TITLE = "📋 <b>نسخه‌های Xray</b>\n\nبرای نصب یک نسخه انتخاب کنید:"
SRV_LOGS_TITLE = "📜 <b>لاگ {type} (آخرین {count})</b>"

# ─── Backup Strings ───────────────────────────────────────────────────────────

BAK_MANAGEMENT = "💾 <b>بکاپ و بازیابی</b>\n\nعملیات مورد نظر را انتخاب کنید:"
BAK_DOWNLOAD_DB = "💾 دانلود دیتابیس"
BAK_DOWNLOAD_CONFIG = "📄 دانلود کانفیگ"
BAK_IMPORT_DB = "📤 ایمپورت دیتابیس"
BAK_BACKUP_TG = "📲 بکاپ به تلگرام"
BAK_DB_CAPTION = "💾 <b>بکاپ دیتابیس</b>\n\nفایل x-ui.db شما:"
BAK_CONFIG_CAPTION = "📄 <b>کانفیگ Xray</b>\n\nفایل config.json شما:"
BAK_IMPORT_PROMPT = (
    "📤 <b>ایمپورت دیتابیس</b>\n\n"
    "فایل <code>.db</code> را ارسال کنید.\n\n"
    "⚠️ این عمل دیتابیس فعلی را <b>جایگزین</b> می‌کند!\n\n"
    "برای لغو /cancel بزنید."
)
BAK_IMPORT_SUCCESS = "✅ <b>دیتابیس با موفقیت ایمپورت شد!</b>\n\nممکن است نیاز به ریستارت پنل باشد."
BAK_TG_SUCCESS = "✅ بکاپ با موفقیت به ربات تلگرام ارسال شد!"

# ─── Online Strings ───────────────────────────────────────────────────────────

ONLINE_TITLE = "📡 <b>کاربران آنلاین ({count})</b>"
ONLINE_EMPTY = "📡 <b>کاربران آنلاین</b>\n\nهیچ کاربری آنلاین نیست."

# ─── Scheduler / Monitor Strings ──────────────────────────────────────────────

SCHED_TRAFFIC_ALERT = (
    "⚠️ <b>هشدار مصرف ترافیک</b>\n\n"
    "کاربر <code>{email}</code> از حجم مجاز فراتر رفته:\n"
    "مصرف: {used} / حد مجاز: {limit}\n\n"
    "🔄 Xray به صورت خودکار ریستارت شد."
)
SCHED_EXPIRY_ALERT = (
    "⏰ <b>هشدار انقضا</b>\n\n"
    "کاربران زیر کمتر از ۲۴ ساعت تا انقضا دارند:\n\n"
    "{clients}"
)
SCHED_XRAY_RESTARTED = "🔄 Xray به دلیل مصرف بیش از حد ترافیک ریستارت شد."
SCHED_STATUS_REPORT = "📊 <b>گزارش دوره‌ای سرور</b>"

# ─── Formatters ───────────────────────────────────────────────────────────────

FMT_UNLIMITED = "♾ نامحدود"
FMT_NEVER = "♾ بدون انقضا"
FMT_EXPIRED = "❌ منقضی شده ({date})"
FMT_EXPIRY = "📅 {date} ({remaining} مانده)"
FMT_EXPIRY_HOURS = "⏰ {date} ({hours} ساعت مانده)"
FMT_DAYS_LEFT = "{days} روز"
FMT_HOURS_LEFT = "{hours} ساعت"
FMT_ENABLED = "✅ فعال"
FMT_DISABLED = "❌ غیرفعال"
FMT_RUNNING = "✅ در حال اجرا"
FMT_STOPPED = "❌ متوقف"
FMT_USED = "📊 مصرف: {used}"
FMT_LIMIT = "📦 حد مجاز: {limit}"
FMT_UPLOAD = "↑ {size}"
FMT_DOWNLOAD = "↓ {size}"
FMT_CLIENT_COUNT = "{count} کاربر"

# ─── Common ───────────────────────────────────────────────────────────────────

ERROR = "❌ خطا: {error}"
FAILED = "❌ عملیات ناموفق: {msg}"
ACCESS_DENIED = "⛔ شما اجازه دسترسی ندارید."
INVALID_INPUT = "❌ ورودی نامعتبر. لطفاً دوباره تلاش کنید."
OPERATION_CANCELLED = "❌ عملیات لغو شد."
CONFIRM_ACTION = "آیا مطمئن هستید؟"

# 🛡️ IranShield Rules — قوانین ایرانی + مسدودسازی تبلیغات برای sing-box و Xray

یک ریپوی شخصی و قابل Fork برای ساخت فهرست‌های **BLOCK تبلیغات** و **DIRECT ایران** که هر ماه با GitHub Actions به‌روز می‌شود و خروجی‌های مستقل برای **sing-box** و **Xray (v2rayN / v2rayNG)** دارد.

> **شروع سریع:** فایل‌های پروژه را در یک مخزن GitHub روی شاخه `main` آپلود کنید؛ سپس `Actions` → `Monthly IranShield Rules Update` → `Run workflow` را یک بار اجرا کنید. بدون اجرای موفق Workflow، فایل‌های خروجی `dist/` هنوز وجود ندارند. برای استفاده از لینک‌های مستقیم `raw.githubusercontent.com` بهتر است مخزن عمومی (public) باشد. مخزن خصوصی برای مصرف از راه دور نیاز به روش احراز هویت دارد؛ توکن را در URL نگذارید.

## قابلیت‌ها

- **BLOCK**: یکپارچه‌سازی AdGuard DNS، StevenBlack، GoodbyeAds، uBOPa و تبلیغات Iran Hosted Domains. قوانین پرتکرار حذف می‌شوند. قوانین مستثنا و لیست سفید، از مسدودکردن اشتباه جلوگیری می‌کنند.
- **DIRECT**: مجموعه دامنه‌های ایران از Iran Hosted Domains (شامل دامنه‌های غیر `.ir` که در ایران میزبانی می‌شوند)، تمامی دامنه‌های با پسوند `.ir`، و تخصیص‌های IPv4/IPv6 ایران بر اساس RIPEstat.
- **sing-box**: سورس `*.json` طبق Rule-Set Source Format و کامپایل خودکار `*.srs` با نسخه رسمی sing-box (نسخه ثابت و بررسی SHA-256).
- **Xray**: `iranshield-geosite.dat` و `iranshield-geoip.dat` اختصاصی (بدون حذف دسته‌های پیش‌فرض فایل‌های `geosite.dat`/`geoip.dat` نرم‌افزار).
- **شفافیت**: `manifest.json` با تعداد آیتم‌ها، هش فایل‌ها و وضعیت منابع؛ `discovered-sources.json` برای یافتن پروژه‌های به‌روز جهت **بررسی دستی**.
- **ایمنی**: شکست منبع ضروری یا خروجی ناقص باعث توقف انتشار می‌شود؛ فایل‌های قبلی در GitHub تا اجرای موفق بعدی باقی می‌مانند.

## نقشه فایل‌های خروجی (پس از اولین اجرای موفق)

```text
dist/
├── srslist.json                       # کلید ↔ لینک مستقیم SRS، شبیه نمونه شما
├── assets.json                        # لینک خروجی همه هسته‌ها و plain/hosts
├── manifest.json                      # تعداد، آدرس/مجوز منبع، SHA-256
├── discovered-sources.json            # کشف کاندیداها، نه افزودن خودکار آنها
├── sing-box/
│   ├── block-ads.json / .srs          # تبلیغات ایران و خارج => BLOCK
│   ├── block-ads-ir.json / .srs       # فقط منابع ایرانی
│   ├── block-ads-global.json / .srs   # فقط منابع بین‌المللی
│   ├── direct-iran-domains.json / .srs # ایرانی + تمام .ir => DIRECT
│   ├── direct-iran-ips.json / .srs     # IPv4 و IPv6 ایران => DIRECT
│   └── direct-iran-all.json / .srs     # ترکیبی => DIRECT
├── plain/                             # ads.txt، ads-ir.txt، iran-domains.txt، iran-ips.txt و ...
├── hosts/                             # فایل hosts برای ابزارهای DNS-level
├── xray/
│   ├── iranshield-geosite.dat         # ADS, ADS-IR, ADS-GLOBAL, IR
│   └── iranshield-geoip.dat           # IR
└── examples/
    ├── singbox-route-fragment.json
    ├── xray-routing-fragment.json
    └── v2rayN-custom-routing.json
```

## تنظیم GitHub — فقط یک بار

1. در GitHub یک مخزن تازه با نام اختیاری `IranShield-Rules` بسازید (نام واقعی می‌تواند متفاوت باشد). محتویات این پروژه را در ریشه شاخه `main` قرار دهید (خود پوشه را به‌صورت زیرپوشه آپلود نکنید).
2. از منوی `Actions`، در صورت نیاز Workflowها را فعال کنید و `Monthly IranShield Rules Update` را با دکمه `Run workflow` اجرا کنید. انتظار می‌رود منابع اینترنتی و نسخه رسمی sing-box در runner قابل دسترسی باشند.
3. پس از موفقیت، فایل‌های `dist/` به همان ریپو commit می‌شوند. لینک‌های `srslist.json` به طور خودکار از مقدار واقعی `${{ github.repository }}` ساخته می‌شوند؛ نیازی به ویرایش دستی نام کاربری نیست.
4. به‌روزرسانی بعدی **روز پنجم هر ماه ساعت 03:17 UTC** اجرا می‌شود. امکان اجرای دستی در هر زمان هم وجود دارد. GitHub ممکن است اجرای زمان‌بندی‌شده را با تأخیر انجام دهد یا در مخزن غیرفعال غیرفعال کند.
5. برای تغییر منابع `config/sources.json`، و برای سفارشی‌سازی `config/blocklist.txt`، `config/allowlist.txt`، `config/direct-domains.txt` و `config/direct-ip.txt` را ویرایش کنید. سپس Workflow را دوباره اجرا کنید.

## لینک‌های استفاده

بعد از آپلود و نخستین اجرای موفق، در آدرس‌های زیر `OWNER` و `REPO` را با نام کاربری/سازمان و نام ریپوی واقعی خودتان جایگزین کنید:

```text
https://raw.githubusercontent.com/OWNER/REPO/main/dist/srslist.json
https://raw.githubusercontent.com/OWNER/REPO/main/dist/assets.json
https://raw.githubusercontent.com/OWNER/REPO/main/dist/sing-box/block-ads.srs
https://raw.githubusercontent.com/OWNER/REPO/main/dist/sing-box/direct-iran-all.srs
https://raw.githubusercontent.com/OWNER/REPO/main/dist/xray/iranshield-geosite.dat
https://raw.githubusercontent.com/OWNER/REPO/main/dist/xray/iranshield-geoip.dat
```

در `srslist.json` کلیدهای آشنایی مثل `geosite-category-ads-all`, `geosite-ads-ir`, `geosite-ir`, `geoip-ir` به فایل‌های SRS اختصاصی این ریپو نگاشت می‌شوند.

## استفاده در sing-box

فایل ساخته‌شده `dist/examples/singbox-route-fragment.json` شامل قطعه آماده `route.rules` و `route.rule_set` است. آن را در تنظیمات موجود خود **ادغام** کنید؛ یک کانفیگ کامل با outbound/این‌باند و DNS نیست. لازم است outbound با برچسب `direct` وجود داشته باشد. `reject` در نسخه‌های جدید sing-box اتصال تبلیغاتی را رد می‌کند؛ اگر از نسخه قدیمی استفاده می‌کنید باید منطق متناسب با همان نسخه را اعمال کنید.

ترتیب مهم است: **تبلیغات (REJECT) → شبکه خصوصی (DIRECT) → ایران (DIRECT) → قوانین دیگر/پروکسی**. برای تشخیص IPهای کشور ممکن است به DNS مناسب و تنظیمات sniffing/routing درست در کلاینت نیاز داشته باشید. تنظیم DNS نادرست، rule-set را جبران نمی‌کند.

نمونه کوتاه برای ترکیب در تنظیمات خود:

```json
{
  "route": {
    "rules": [
      {"rule_set": ["block-ads"], "action": "reject"},
      {"rule_set": ["direct-iran-all"], "action": "route", "outbound": "direct"}
    ],
    "rule_set": [
      {"type": "remote", "tag": "block-ads", "format": "binary", "url": "https://raw.githubusercontent.com/OWNER/REPO/main/dist/sing-box/block-ads.srs"},
      {"type": "remote", "tag": "direct-iran-all", "format": "binary", "url": "https://raw.githubusercontent.com/OWNER/REPO/main/dist/sing-box/direct-iran-all.srs"}
    ]
  }
}
```

## استفاده در v2rayN (Xray)

1. فایل‌های `dist/xray/iranshield-geosite.dat` و `dist/xray/iranshield-geoip.dat` را از صفحه GitHub خود دانلود کنید و در **مسیر assets/resource فایل‌های Xray** قرار دهید (مسیر دقیق به نسخه v2rayN و هسته انتخابی بستگی دارد). فایل‌های پیش‌فرض کلاینت را پاک نکنید.
2. خروجی `dist/examples/v2rayN-custom-routing.json` را از بخش **Routing → Custom routing / Import** (نام منو ممکن است تغییر کند) وارد کنید یا چهارتا قانون زیر را به ترتیب در تنظیمات Routing اضافه کنید:
   - `domain: ext:iranshield-geosite.dat:ADS` → `block`
   - `ip: geoip:private` → `direct`
   - `domain: ext:iranshield-geosite.dat:IR` → `direct`
   - `ip: ext:iranshield-geoip.dat:IR` → `direct`
3. خروجی پروکسی پیش‌فرض خود را حفظ کنید و گزینه `domainStrategy` را متناسب با نیاز روی `IPIfNonMatch` تنظیم کنید. کلاینت را دوباره راه‌اندازی کنید.

**نکته:** این فایل یک نمونه Routing است، **subscription سرور VLESS/VMess نیست**؛ آن را به‌عنوان اشتراک سرور وارد نکنید.

## استفاده در v2rayNG (Android، هسته Xray)

1. در نسخه‌های پشتیبانی‌کننده، از `Geo asset files` یا روش قرار دادن فایل‌های `.dat` در پوشه assets مخصوص برنامه استفاده کنید. مسیر معمول `Android/data/com.v2ray.ang/files/assets` است، ولی در نسخه‌ها و گوشی‌های جدید ممکن است متفاوت/غیرقابل دسترسی باشد. فایل‌های اختصاصی را با نام `iranshield-...` در کنار فایل‌های اصلی قرار دهید.
2. وارد `Routing Settings` شوید؛ قوانین `domain` و `ip` را مطابق چهار قانون بالا ایجاد کنید. اگر برنامه واردکردن `ruleset from clipboard` را پشتیبانی می‌کند، می‌توانید آرایه `v2rayN-custom-routing.json` را امتحان کنید؛ در غیر این صورت قوانین را دستی بسازید.
3. ترتیب را رعایت کنید (BLOCK بالاتر از DIRECT). بعضی نسخه‌ها دانلود مستقیم Rule-set سفارشی را فراهم نمی‌کنند؛ تغییر فایل‌های assets و ارجاع `ext:` باید واقعاً توسط هسته کلاینت پشتیبانی شود.

## اجرا و تست محلی

Python 3.12+ لازم است؛ بدون وابستگی PyPI. برای نمونه **بدون اینترنت**:

```bash
python -m unittest discover -s tests -v
python scripts/build.py --fixtures tests/fixtures --out .temp/sample-dist --repository yourname/IranShield-Rules
```

برای خروجی واقعی (نیازمند اینترنت) `python scripts/build.py --repository yourname/IranShield-Rules`، سپس کامپایل همه فایل‌های JSON با `sing-box rule-set compile` و در انتها `python scripts/finalize.py dist` اجرا شود. مسیر ساده‌تر، اجرای Workflow است.

## کنترل کیفیت، حریم خصوصی و محدودیت‌ها

- `config/sources.json` **منابع معتبر بازبینی‌شده** است. اسکریپت `discover.py` هر ماه ریپوهای فعال و معروف GitHub را جست‌وجو و فهرست می‌کند؛ **بدون بررسی مجوز، صحت محتوا و ریسک false positive، منبع ناشناخته را خودکار به BLOCK اضافه نمی‌کند**. برای اضافه‌کردن منبع جدید، آن را با نوع فرمت و `min_entries` به config اضافه کنید.
- فیلترهای CSS، HTML، اسکریپتی، آدرس‌های path-specific و استثناهای با modifier پیچیده در uBlock/AdGuard به قوانین سطح دامنه قابل تبدیل مطمئن نیستند؛ عمداً حذف می‌شوند. بنابراین «۱۰۰٪ همه تبلیغات» با Xray یا sing-box امکان‌پذیر نیست. برای تبلیغات تزریق‌شده در همان دامنه سایت، افزونه مرورگر uBlock Origin مکمل خوبی است.
- داده IP از تخصیص‌ها و ثبت‌های RIPE می‌آید؛ **تضمین نمی‌کند هر IP در این مجموعه از نظر جغرافیایی داخل ایران باشد**. میزبانی و مسیرها تغییر می‌کنند. برخی آی‌پی‌های داخل ایران ممکن است خارج از این داده باشند.
- برخی فهرست‌ها مجوز انتشار مجدد متفاوت دارند. مجوز منابع در `config/sources.json` و `manifest.json` ذکر می‌شود. فهرست‌های دارای محدودیت بازنشر مثل بعضی نسخه‌های Hagezi یا داده‌های IPdeny عمداً وارد خروجی نشده‌اند. داده‌های تبدیل‌شده AdGuard تابع GPL-3.0 هستند؛ استفاده یا بازنشر را مطابق مجوز هر منبع انجام دهید. پروژه با هیچ منبعی وابستگی رسمی ندارد.
- برای یک ریپوی **کاملاً خصوصی**، فایل‌های `remote` بدون احراز هویت دانلود نخواهند شد؛ فایل‌های SRS را محلی بارگیری کنید یا برای انتشار عمومی یک ریپوی جدا داشته باشید.
- گاهی GitHub Actions یا یک منبع از دسترس خارج می‌شوند؛ با fail-closed شدن بیلد، فایل خروجی قبلی به قوت خود باقی می‌ماند. `manifest.json` را برای آخرین اجرای موفق بررسی کنید.

## منابع اصلی

| پروژه | نقش | پیوند |
|---|---|---|
| AdGuard DNS Filter | تبلیغات جهانی / ردیاب DNS | https://github.com/AdguardTeam/AdGuardSDNSFilter |
| StevenBlack hosts | تبلیغات جهانی | https://github.com/StevenBlack/hosts |
| GoodbyeAds | hosts تبلیغات جهانی | https://github.com/jerryn70/GoodbyeAds |
| uBOPa | تبلیغات فارسی DNS-convertible | https://github.com/nimasaj/uBOPa |
| Iran Hosted Domains | دامنه‌های ایران + تبلیغات منطقه‌ای | https://github.com/bootmortis/iran-hosted-domains |
| RIPEstat | رنج‌های IP ایران | https://stat.ripe.net/ |

## مجوز

کد و فایل‌های اصلی پروژه تحت **GPL-3.0** منتشر می‌شوند (فایل `LICENSE`). حقوق فهرست‌های ثالث و مجوزهای مختص آن‌ها محفوظ است؛ به‌ویژه خروجی ترکیبی نباید برخلاف شرایط بازنشر منابع منتشر شود.

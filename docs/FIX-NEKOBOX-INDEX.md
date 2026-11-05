# رفع خطای انتشار `dist/nekobox/srslist.json`

## خطای قبلی

```text
cp: cannot stat 'dist/nekobox/srslist.json': No such file or directory
```

**علت:** بعضی نسخه‌های اسکریپت ساخت فایل `dist/nekobox/srslist.json` را تولید نمی‌کنند، ولی Workflow قدیمی فرض می‌کند حتماً ساخته شده است.

## اصلاح قطعی در فایل YAML

فایل `.github/workflows/update-rules.yml` جدید **به‌تنهایی** حاوی کد پایتون لازم برای تولید فهرست است؛ نیازی به نصب بستهٔ اضافی یا افزودن اسکریپت جدید برای این اصلاح ندارد.

پس از کامپایل ۶ فایل SRS، Workflow چهار نسخهٔ یکسان می‌سازد:

- `srslist.json` (ریشهٔ ریپو)
- `nekobox/srslist.json`
- `dist/srslist.json`
- `dist/nekobox/srslist.json`

هر JSON شامل ۱۲ نام متداول و URL واقعی فایل SRS در ریپوی اجراکننده است. اگر فایل SRS ناقص باشد، مرحلهٔ جدید با اعلام نام آن متوقف می‌شود؛ انتشار ناقص صورت نمی‌گیرد. سپس اسکریپت `finalize.py` اجرا شده، صحت JSON و برابر بودن ۴ کپی کنترل می‌شود و فایل‌ها commit می‌شوند.

## روش اعمال

1. در GitHub به `.github/workflows/update-rules.yml` بروید و محتوایش را با نسخهٔ اصلاح‌شده جایگزین کنید و `Commit changes` بزنید.
2. به `Actions` بروید، `Twice-Monthly IranShield Rules Update` را انتخاب و `Run workflow` را کلیک کنید.
3. اگر همهٔ مراحل سبز شدند، آدرس ثابت JSON زیر را باز کنید:

```text
https://raw.githubusercontent.com/ReCode1324/IranShield-Rules/main/srslist.json
```

اگر شاخهٔ پیش‌فرض شما `main` نیست، نام شاخهٔ واقعی را در لینک تغییر دهید. زمان‌بندی روزهای ۱ و ۱۵ هر ماه، ساعت 03:17 UTC برقرار است.

**توجه:** تغییرات باید در GitHub حساب شما commit شوند؛ صرف دانلود ZIP اجرای GitHub Actions را عوض نمی‌کند. برای `git push` خودکار، مجوز `contents: write` فعال و محدودیت محافظت از شاخه بررسی شود. اگر ریپو Private باشد، raw URL عمومی بدون احراز هویت کار نمی‌کند.

# سفارشی‌سازی و اضافه‌کردن منابع

فهرست منابع در `config/sources.json` است. منبع جدید باید HTTPS، سازگار با یکی از قالب‌های `hosts`، `adblock`، `clash`، `domains`، `cidr` یا `ripe-json`، و دارای مجوز بازنشر مشخص باشد.

- افزودن بلاک: `config/blocklist.txt`
- رفع false positive: `config/allowlist.txt`
- دامنه‌های مستقیم سفارشی: `config/direct-domains.txt`
- رنج IP مستقیم سفارشی: `config/direct-ip.txt`

برای هر تغییر تست بزنید: `python -m unittest discover -s tests -v`؛ سپس workflow دستی اجرا کنید. `dist/discovered-sources.json` فقط کاندیداهای دارای مشخصات عمومی را نشان می‌دهد، نه مجوز افزودن خودکار. درخواست‌های ناشناس و قواعد wildcard/regex بدون بازبینی پذیرفته نمی‌شوند.

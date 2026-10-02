# استقرار روی سرور مشترک Cloubit VPS

مرجع معماری: README «معماری سرور Cloubit VPS» (Docker + یک Caddy مشترک + هر پروژه یک استک مستقل). این سند همان الگو را برای سان اپ اعمال می‌کند.

| مورد | مقدار |
| --- | --- |
| سرور | `87.107.102.248` (Ubuntu 24.04؛ دسترسی با `ssh vps4`) |
| پنل ادمین | `https://panel.saanapp.ir` ← کانتینر `saanapp-panel:80` |
| اپ موبایل (PWA) | `https://web.saanapp.ir` ← کانتینر `saanapp-web:80` |
| بک‌اند (API) | `https://webapi.saanapp.ir` ← کانتینر `saanapp-api:8000` |
| مسیر پروژه | `/opt/apps/saanapp` (کلون مخزن + `.env`) |
| فایل Caddy | `/opt/proxy/sites/saanapp.caddy` |
| استک | PostgreSQL 16 + Django/gunicorn + دو nginx برای فرانت‌ها (`infra/docker-compose.prod.yml`) |

## قواعد ایمنی (چون چند پروژه دیگر روی همین سرور اجرا می‌شوند)

- فقط داخل `/opt/apps/saanapp` و پروژه compose با نام `saanapp` کار کنید. هیچ‌وقت `docker compose down`، `docker system prune`، `docker volume prune` یا `docker network rm` روی کل سرور اجرا نکنید.
- پورتی روی هاست منتشر نمی‌شود؛ فقط Caddy عمومی است. سرویس‌های عمومی با aliasهای یکتا `saanapp-api|panel|web` به شبکه مشترک `web` وصل می‌شوند.
- فایل Caddy این پروژه جداست (`sites/saanapp.caddy`). پیش از reload حتماً `caddy validate` بزنید؛ reload گراف است و اگر کانفیگ خراب باشد رد می‌شود.
- build یک‌به‌یک و با اولویت پایین انجام می‌شود (سقف heap برای Node، `nice`) و هر سرویس سقف حافظه دارد (db ۵۱۲MB، api ۷۶۸MB، هر nginx ۱۲۸MB). حافظه سرور ~۸GB است و پروژه‌های دیگر ~۲٫۵GB را مصرف می‌کنند.
- لاگ هر سرویس با چرخش ۳×۱۰MB محدود است.

## استقرار اول

DNS هر سه دامنه باید به IP سرور اشاره کند (با `getent hosts` روی سرور بررسی کنید).

```bash
ssh vps4
git clone https://git.cloubit.com/saanapp/mono.git /opt/apps/saanapp -b test   # نیازمند دسترسی مخزن
cd /opt/apps/saanapp
cp infra/saanapp.env.example .env && chmod 600 .env
# DJANGO_SECRET_KEY و DATABASE_PASSWORD را تصادفی بسازید:  openssl rand -hex 32  /  openssl rand -hex 16
sh infra/deploy.sh --no-pull

# Caddy: فایل جدید + اعتبارسنجی + reload
cp infra/saanapp.caddy /opt/proxy/sites/saanapp.caddy
docker compose -f /opt/proxy/compose.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose -f /opt/proxy/compose.yml exec caddy caddy reload   --config /etc/caddy/Caddyfile
```

### راه‌اندازی اولیه داده

دیتابیس تازه نقش، منو و کاربر ندارد. یک‌بار این فرمان را اجرا کنید (رمز از متغیر `BOOTSTRAP_ADMIN_PASSWORD` خوانده می‌شود و چاپ نمی‌شود؛ حداقل ۸ نویسه و نه رایج/عددی):

```bash
docker compose --project-name saanapp --env-file .env -f infra/docker-compose.prod.yml exec \
  -e BOOTSTRAP_ADMIN_PASSWORD='...' api \
  python manage.py bootstrap_saan --admin-phone 09xxxxxxxxx --admin-name "نام و نام خانوادگی"
```

پروژه، هفت نقش (مدیر کل، برنامه‌ریز، پشتیبان، انباردار، کارشناس میدانی، مدیر ساختمان، نماینده مشتری) با دسترسی‌های هر کدام، منوهای ادمین (در همان ساختار کوتاه‌شده با تب‌ها) و منوی اپ میدانی و اولین مدیر (ابرکاربر) ساخته می‌شود. اجرای دوباره چیزی را که تغییر داده‌اید بازنویسی نمی‌کند (`--refresh-grants` و `--refresh-menus` برای بازنویسی صریح). سپس از ادمین Django (`/coreadminurl/` روی `webapi.saanapp.ir`) یا API، داده کسب‌وکار (انواع خدمت، پرسشنامه‌ها، ساختمان‌ها و آسانسورها) را بسازید.

## به‌روزرسانی

```bash
ssh vps4 /opt/apps/saanapp/infra/deploy.sh
```

اگر مهاجرت دیتابیس داشته باشد، هنگام بالا آمدن API خودکار اجرا می‌شود (`docker-entrypoint.sh`). قبل از تغییر بزرگ پشتیبان بگیرید:

```bash
docker compose --project-name saanapp --env-file .env -f infra/docker-compose.prod.yml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > /root/backups/saanapp-$(date +%F-%H%M).sql.gz
```

## وظایف زمان‌بندی‌شده

سرویس ادواری و یادآوری موعد با یک فرمان روزانه کار می‌کند؛ از cron میزبان:

```cron
10 6 * * * cd /opt/apps/saanapp && docker compose --project-name saanapp --env-file .env -f infra/docker-compose.prod.yml exec -T api python manage.py run_field_schedules >> /var/log/saanapp-schedules.log 2>&1
```

## عیب‌یابی

| کار | دستور |
| --- | --- |
| وضعیت | `docker compose --project-name saanapp --env-file .env -f infra/docker-compose.prod.yml ps` |
| لاگ API | `... logs -f --tail=100 api` |
| لاگ Caddy | `docker compose -f /opt/proxy/compose.yml logs --tail=50 caddy` |
| سلامت | `curl -sI https://webapi.saanapp.ir/health/ \| head -1` |

- **خطای CORS در مرورگر:** `DJANGO_CORS_ALLOWED_ORIGINS` باید هر دو دامنه فرانت را داشته باشد؛ بعد از تغییر `.env` فقط `up -d api` بزنید.
- **فرانت به آدرس اشتباه وصل می‌شود:** آدرس API در build داخل bundle ثابت می‌شود (`VUE_APP_SAAN_APP_PATH`)؛ با تغییر آن فرانت‌ها را دوباره build کنید.
- **گواهی SSL صادر نمی‌شود:** DNS یا پورت ۸۰/۴۴۳؛ لاگ Caddy را ببینید.

## محدودیت‌ها و کارهای باز

- فایل‌های بارگذاری‌شده (عکس‌های کارشناس) روی volume `media-data` ذخیره و فقط با لینک امضاشده ۵ دقیقه‌ای خوانده می‌شوند. اگر بعداً storage شیء (Arvan/MinIO) بخواهید، `LOCAL_MEDIA_STORAGE=false` و متغیرهای `GENERAL_ARVAN_STORAGE_*` را تنظیم کنید. این volume را در پشتیبان‌گیری سرور لحاظ کنید.
- پیامک (OTP، پرسشنامه) و کیف پول بدون اعتبارنامه کار نمی‌کنند: `FARAPAYAMAK_*` و `WALLET_*` را فقط در `.env` سرور بگذارید. ورود با نام کاربری و رمز بدون پیامک کار می‌کند. کلیدهای قدیمی مخزن باید چرخانده شوند ([REPOSITORY_SYNC](REPOSITORY_SYNC.md)).
- فایل‌های استاتیک ادمین Django (`/coreadminurl/`) سرو نمی‌شوند و صفحه ساده دیده می‌شود؛ ابزار روزمره پنل `panel.saanapp.ir` است.
- Swagger/Redoc در production خاموش است.

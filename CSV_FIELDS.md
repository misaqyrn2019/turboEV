# راهنمای فیلدهای CSV

فایل CSV با UTF-8 ذخیره شود. مقدار وضعیت‌ها از کلیدهای جدول استفاده می‌کند. ارتباط‌ها با code رکورد مرتبط وارد می‌شوند.

## centers - مراکز توزیع

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | نام | text | بله |  |
| city | شهر | text | بله |  |
| address | نشانی | textarea | خیر |  |
| manager | مسئول مرکز | text | خیر |  |
| phone | تلفن | text | خیر |  |
| latitude | عرض جغرافیایی | number | خیر |  |
| longitude | طول جغرافیایی | number | خیر |  |
| power_kw | ظرفیت برق (کیلووات) | number | بله |  |
| safety_approved | تأیید ایمنی سایت | checkbox | خیر |  |
| status | وضعیت | select | بله | active = فعال; inactive = غیرفعال |
| notes | توضیحات | textarea | خیر |  |

## fleets - ناوگان

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | نام | text | بله |  |
| center_id | مرکز توزیع | reference | بله | centers |
| owner | مالک / بهره‌بردار | text | خیر |  |
| service_owner | مسئول فنی توسن | text | خیر |  |
| mission_scope | محدوده مأموریت | text | خیر |  |
| status | وضعیت | select | بله | active = فعال; inactive = غیرفعال |
| notes | توضیحات | textarea | خیر |  |

## drivers - رانندگان

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | نام | text | بله |  |
| phone | تلفن همراه | text | خیر |  |
| license | شماره گواهینامه | text | خیر |  |
| center_id | مرکز توزیع | reference | بله | centers |
| trained | آموزش و تحویل تأیید شده | checkbox | خیر |  |
| status | وضعیت | select | بله | active = فعال; inactive = غیرفعال |
| notes | توضیحات | textarea | خیر |  |

## batteries - باتری‌ها

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| model | مدل | text | بله |  |
| serial | شماره سریال | text | خیر |  |
| center_id | مرکز توزیع | reference | بله | centers |
| chemistry | نوع باتری | select | بله | lithium = لیتیوم یون; lfp = لیتیوم آهن فسفات; lead = سرب اسید |
| capacity_kwh | ظرفیت (کیلووات‌ساعت) | number | خیر |  |
| soc | سطح شارژ SOC (%) | number | خیر |  |
| soh | سلامت SOH (%) | number | خیر |  |
| temperature | دمای باتری (°C) | number | خیر |  |
| cycles | چرخه شارژ | number | بله |  |
| status | وضعیت | select | بله | healthy = سالم; inspection = نیازمند بررسی; critical = بحرانی; inactive = غیرفعال |
| bms_error | کد خطای BMS | text | خیر |  |
| bms_critical | خطای بحرانی BMS | checkbox | خیر |  |
| measured_at | زمان اندازه‌گیری | datetime-local | خیر |  |
| warranty_until | پایان گارانتی | date | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## vehicles - موتورسیکلت‌ها

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| model | مدل موتور | text | بله |  |
| type | نوع موتور | select | بله | electric = برقی; gasoline = بنزینی |
| plate | پلاک | text | خیر |  |
| vin | شماره شاسی / VIN | text | خیر |  |
| fleet_id | ناوگان | reference | بله | fleets |
| driver_id | راننده اصلی | reference | خیر | drivers |
| battery_id | باتری | reference | خیر | batteries |
| odometer | کیلومترشمار | number | بله |  |
| ownership | نوع مالکیت | select | بله | owned = ملکی; contract = پیمانکاری; lease = اجاره‌ای |
| purchase_date | تاریخ خرید | date | خیر |  |
| purchase_price | مبلغ خرید (تومان) | number | بله |  |
| supplier | فروشنده / تأمین‌کننده | text | خیر |  |
| invoice | شماره فاکتور | text | خیر |  |
| warranty_until | پایان گارانتی | date | خیر |  |
| support_owner | مسئول پشتیبانی | text | خیر |  |
| gps_id | شناسه GPS | text | خیر |  |
| last_location | آخرین موقعیت ثبت‌شده | text | خیر |  |
| status | وضعیت پایه | select | بله | ready = آماده سرویس; maintenance = نیازمند سرویس; out = خارج از سرویس |
| safety_checked | ایمنی و بازرسی تأیید شده | checkbox | خیر |  |
| charger_checked | سازگاری شارژر تأیید شده | checkbox | خیر |  |
| data_checked | شناسه و دسترسی داده تأیید شده | checkbox | خیر |  |
| support_checked | پشتیبانی و گارانتی تأیید شده | checkbox | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## chargers - شارژرها

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | نام | text | بله |  |
| center_id | مرکز توزیع | reference | بله | centers |
| power_kw | توان (کیلووات) | number | بله |  |
| connector | نوع اتصال / سازگاری | text | خیر |  |
| status | وضعیت | select | بله | ready = آماده; fault = خراب; inactive = غیرفعال |
| error_code | کد خطا | text | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## charges - مدیریت شارژ

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| vehicle_id | موتورسیکلت | reference | بله | vehicles |
| charger_id | شارژر | reference | بله | chargers |
| operator | اپراتور | text | خیر |  |
| status | وضعیت | select | بله | queued = در صف; charging = در حال شارژ; completed = تکمیل شده; failed = ناموفق; cancelled = لغو شده |
| started_at | شروع شارژ | datetime-local | خیر |  |
| ended_at | پایان شارژ | datetime-local | خیر |  |
| soc_start | شارژ اولیه (%) | number | خیر |  |
| soc_end | شارژ نهایی (%) | number | خیر |  |
| energy_kwh | انرژی مصرفی (کیلووات‌ساعت) | number | خیر |  |
| error_code | کد خطا | text | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## shifts - شیفت‌ها

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | نام | text | بله |  |
| center_id | مرکز توزیع | reference | بله | centers |
| start_time | ساعت شروع | time | بله |  |
| end_time | ساعت پایان | time | بله |  |
| days | روزهای هفته | days | خیر |  |
| driver_ids | رانندگان | multi-reference | خیر | drivers |
| status | وضعیت | select | بله | active = فعال; inactive = غیرفعال |
| notes | توضیحات | textarea | خیر |  |

## missions - مأموریت‌ها

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | عنوان مأموریت | text | بله |  |
| vehicle_id | موتورسیکلت | reference | بله | vehicles |
| driver_id | راننده | reference | بله | drivers |
| center_id | مرکز توزیع | reference | بله | centers |
| shift_id | شیفت | reference | خیر | shifts |
| route | مسیر / منطقه | text | خیر |  |
| category | دسته مأموریت | text | خیر |  |
| load_kg | وزن بار (کیلوگرم) | number | بله |  |
| status | وضعیت | select | بله | planned = برنامه‌ریزی شده; active = در حال اجرا; completed = تکمیل شده; delayed = با تأخیر; failed = ناموفق; cancelled = لغو شده |
| started_at | زمان شروع | datetime-local | خیر |  |
| due_at | مهلت تحویل | datetime-local | خیر |  |
| ended_at | زمان پایان | datetime-local | خیر |  |
| distance_km | مسافت (کیلومتر) | number | خیر |  |
| soc_start | شارژ آغاز (%) | number | خیر |  |
| soc_end | شارژ پایان (%) | number | خیر |  |
| result | نتیجه مأموریت | textarea | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## incidents - خرابی‌ها

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| title | عنوان خرابی | text | بله |  |
| vehicle_id | موتورسیکلت | reference | بله | vehicles |
| battery_id | باتری | reference | خیر | batteries |
| category | نوع خرابی | select | بله | battery = باتری; bms = سیستم BMS; electrical = برق; mechanical = مکانیکی; charger = شارژر; other = سایر |
| severity | شدت | select | بله | critical = بحرانی; high = مهم; low = جزئی |
| status | وضعیت | select | بله | open = باز; acknowledged = تأیید دریافت; repairing = در حال تعمیر; waiting = در انتظار قطعه; resolved = رفع شده; closed = بسته شده |
| owner | مسئول رسیدگی | text | بله |  |
| reported_at | زمان وقوع | datetime-local | بله |  |
| responded_at | زمان پاسخ | datetime-local | خیر |  |
| repair_started_at | شروع تعمیر | datetime-local | خیر |  |
| resolved_at | رفع خرابی | datetime-local | خیر |  |
| restored_at | بازگشت به سرویس | datetime-local | خیر |  |
| root_cause | علت ریشه‌ای | textarea | خیر |  |
| resolution | اقدام اصلاحی / شرط بازگشت | textarea | خیر |  |
| cost | هزینه تعمیر (تومان) | number | بله |  |
| next_action | اقدام بعدی / تشدید | text | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## tickets - پشتیبانی و SLA

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| title | موضوع درخواست | text | بله |  |
| vehicle_id | موتورسیکلت | reference | خیر | vehicles |
| incident_id | رخداد مرتبط | reference | خیر | incidents |
| center_id | مرکز توزیع | reference | بله | centers |
| priority | اولویت | select | بله | critical = بحرانی; high = مهم; low = جزئی |
| status | وضعیت | select | بله | open = باز; progress = در حال بررسی; waiting = در انتظار قطعه; answered = پاسخ داده شده; closed = بسته شده |
| owner | کارشناس مسئول | text | بله |  |
| reported_at | زمان ثبت | datetime-local | بله |  |
| responded_at | زمان اولین پاسخ | datetime-local | خیر |  |
| closed_at | زمان بسته شدن | datetime-local | خیر |  |
| response | پاسخ / نتیجه | textarea | خیر |  |
| escalation | ارجاع / تشدید | text | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## checks - کنترل پیش از شیفت

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| vehicle_id | موتورسیکلت | reference | بله | vehicles |
| driver_id | راننده | reference | بله | drivers |
| shift_id | شیفت | reference | خیر | shifts |
| checked_at | زمان کنترل | datetime-local | بله |  |
| visual_ok | بازرسی ظاهری و ایمنی | checkbox | خیر |  |
| battery_ok | باتری و BMS بدون خطای بحرانی | checkbox | خیر |  |
| charger_ok | شارژر سازگار و سالم | checkbox | خیر |  |
| gps_ok | موقعیت‌یابی و دسترسی داده | checkbox | خیر |  |
| support_ok | پشتیبانی و گارانتی مشخص | checkbox | خیر |  |
| status | نتیجه | select | بله | pending = در انتظار بررسی; passed = تأیید شده; failed = رد شده |
| notes | توضیحات | textarea | خیر |  |

## daily_logs - کارکرد روزانه

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| vehicle_id | موتورسیکلت | reference | بله | vehicles |
| shift_id | شیفت | reference | خیر | shifts |
| date | تاریخ | date | بله |  |
| planned_minutes | زمان خدمت برنامه‌ریزی شده (دقیقه) | number | بله |  |
| available_minutes | زمان آماده‌به‌کاری (دقیقه) | number | بله |  |
| distance_km | پیمایش (کیلومتر) | number | بله |  |
| energy_kwh | انرژی (کیلووات‌ساعت) | number | بله |  |
| fuel_liters | بنزین مصرفی (لیتر) | number | بله |  |
| maintenance_cost | هزینه نگهداری (تومان) | number | بله |  |
| soc_end | شارژ پایان شیفت (%) | number | خیر |  |
| notes | توضیحات | textarea | خیر |  |

## gates - آمادگی پایلوت

| ستون | عنوان | نوع | الزامی | مقادیر / ارتباط |
|---|---|---|---|---|
| code | شناسه | text | بله |  |
| name | نام | text | بله |  |
| owner | مسئول | text | بله |  |
| status | وضعیت | select | بله | open = باز; conditional = مشروط; approved = تأیید شده; rejected = رد شده |
| evidence | شواهد / مرجع | textarea | خیر |  |
| decision | تصمیم / اقدام بعدی | textarea | خیر |  |
| reviewed_at | زمان بررسی | datetime-local | خیر |  |
| notes | توضیحات | textarea | خیر |  |

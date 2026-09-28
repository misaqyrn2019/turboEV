"""Shared, server-owned field definitions for validation, forms and CSV templates."""

def f(key, label, type='text', required=False, **kwargs):
    return dict(key=key, label=label, type=type, required=required, **kwargs)

def sel(key, label, options, default=None, **kwargs):
    return f(key, label, 'select', required=kwargs.pop('required',default is not None), options=[{'value': k, 'label': v} for k,v in options], default=default, **kwargs)

def ref(key, label, source, required=False):
    return f(key, label, 'reference', required, source=source)

def num(key, label, default=0, min=0, max=1e12, **kwargs):
    return f(key, label, 'number', required=kwargs.pop('required',default is not None), default=default, min=min, max=max, **kwargs)

def module(label, singular, icon, fields, columns, description):
    return dict(label=label, singular=singular, icon=icon, fields=fields, columns=columns, description=description)

ACTIVE = [('active','فعال'),('inactive','غیرفعال')]
VSTATUS = [('ready','آماده سرویس'),('maintenance','نیازمند سرویس'),('out','خارج از سرویس')]
SEVERITY = [('critical','بحرانی'),('high','مهم'),('low','جزئی')]
NOTES = f('notes','توضیحات','textarea')
CODE = f('code','شناسه',required=True)
NAME = f('name','نام',required=True)
STATUS = sel('status','وضعیت',ACTIVE,'active')
CATALOG = {
 'centers': module('مراکز توزیع','مرکز توزیع','MapPin',[
    CODE, NAME, f('city','شهر',required=True), f('address','نشانی','textarea'), f('manager','مسئول مرکز'), f('phone','تلفن'), num('latitude','عرض جغرافیایی',None,-90,90),num('longitude','طول جغرافیایی',None,-180,180),num('power_kw','ظرفیت برق (کیلووات)'),f('safety_approved','تأیید ایمنی سایت','checkbox',default=False), STATUS, NOTES
 ], ['code','name','city','manager','status'],'مراکز عملیاتی، مسئولان و آمادگی زیرساخت'),
 'fleets': module('ناوگان','ناوگان','Truck',[
    CODE,NAME,ref('center_id','مرکز توزیع','centers',True),f('owner','مالک / بهره‌بردار'),f('service_owner','مسئول فنی'),f('mission_scope','محدوده مأموریت'),STATUS,NOTES
 ],['code','name','center_id','owner','status'],'مدیریت گروه‌های ناوگان و مراکز عملیاتی'),
 'drivers': module('رانندگان','راننده','Users',[
    CODE, NAME,f('phone','تلفن همراه'),f('license','شماره گواهینامه'),ref('center_id','مرکز توزیع','centers',True),f('trained','آموزش و تحویل تأیید شده','checkbox',default=False),STATUS,NOTES
 ],['code','name','phone','center_id','trained','status'],'پرونده رانندگان، آموزش و تخصیص عملیاتی'),
 'batteries': module('باتری‌ها','باتری','Battery',[
    CODE,f('model','مدل',required=True),f('serial','شماره سریال'),ref('center_id','مرکز توزیع','centers',True),sel('chemistry','نوع باتری',[('lithium','لیتیوم یون'),('lfp','لیتیوم آهن فسفات'),('lead','سرب اسید')],'lithium'),num('capacity_kwh','ظرفیت (کیلووات‌ساعت)',None),num('soc','سطح شارژ SOC (%)',None,0,100),num('soh','سلامت SOH (%)',None,0,100),num('temperature','دمای باتری (°C)',None,-50,150),num('cycles','چرخه شارژ'),sel('status','وضعیت',[('healthy','سالم'),('inspection','نیازمند بررسی'),('critical','بحرانی'),('inactive','غیرفعال')],'healthy'),f('bms_error','کد خطای BMS'),f('bms_critical','خطای بحرانی BMS','checkbox',default=False),f('measured_at','زمان اندازه‌گیری','datetime-local'),f('warranty_until','پایان گارانتی','date'),NOTES
 ],['code','model','center_id','soc','soh','temperature','status'],'پایش شارژ، سلامت و خطاهای سیستم مدیریت باتری'),
 'vehicles': module('موتورسیکلت‌ها','موتورسیکلت','Bike',[
    CODE,f('model','مدل موتور',required=True),sel('type','نوع موتور',[('electric','برقی'),('gasoline','بنزینی')],'electric'),f('plate','پلاک'),f('vin','شماره شاسی / VIN'),ref('fleet_id','ناوگان','fleets',True),ref('driver_id','راننده اصلی','drivers'),ref('battery_id','باتری','batteries'),num('odometer','کیلومترشمار'),sel('ownership','نوع مالکیت',[('owned','ملکی'),('contract','پیمانکاری'),('lease','اجاره‌ای')],'owned'),f('purchase_date','تاریخ خرید','date'),num('purchase_price','مبلغ خرید (تومان)'),f('supplier','فروشنده / تأمین‌کننده'),f('invoice','شماره فاکتور'),f('warranty_until','پایان گارانتی','date'),f('support_owner','مسئول پشتیبانی'),f('gps_id','شناسه GPS'),f('last_location','آخرین موقعیت ثبت‌شده'),sel('status','وضعیت پایه',VSTATUS,'out'),f('safety_checked','ایمنی و بازرسی تأیید شده','checkbox',default=False),f('charger_checked','سازگاری شارژر تأیید شده','checkbox',default=False),f('data_checked','شناسه و دسترسی داده تأیید شده','checkbox',default=False),f('support_checked','پشتیبانی و گارانتی تأیید شده','checkbox',default=False),NOTES
 ],['code','model','type','fleet_id','driver_id','battery_id','odometer','status'],'ثبت خرید و مدیریت چرخه عمر موتورهای برقی و بنزینی'),
 'chargers': module('شارژرها','شارژر','PlugZap',[
    CODE,NAME,ref('center_id','مرکز توزیع','centers',True),num('power_kw','توان (کیلووات)',1),f('connector','نوع اتصال / سازگاری'),sel('status','وضعیت',[('ready','آماده'),('fault','خراب'),('inactive','غیرفعال')],'ready'),f('error_code','کد خطا'),NOTES
 ],['code','name','center_id','power_kw','connector','status'],'ظرفیت و وضعیت تجهیزات شارژ'),
 'charges': module('مدیریت شارژ','نوبت شارژ','Zap',[
    CODE,ref('vehicle_id','موتورسیکلت','vehicles',True),ref('charger_id','شارژر','chargers',True),f('operator','اپراتور'),sel('status','وضعیت',[('queued','در صف'),('charging','در حال شارژ'),('completed','تکمیل شده'),('failed','ناموفق'),('cancelled','لغو شده')],'queued'),f('started_at','شروع شارژ','datetime-local'),f('ended_at','پایان شارژ','datetime-local'),num('soc_start','شارژ اولیه (%)',None,0,100),num('soc_end','شارژ نهایی (%)',None,0,100),num('energy_kwh','انرژی مصرفی (کیلووات‌ساعت)',None),f('error_code','کد خطا'),NOTES
 ],['code','vehicle_id','charger_id','started_at','energy_kwh','soc_start','soc_end','status'],'مدیریت صف شارژ و ثبت زمان و انرژی هر نوبت'),
 'shifts': module('شیفت‌ها','شیفت','CalendarClock',[
    CODE,NAME,ref('center_id','مرکز توزیع','centers',True),f('start_time','ساعت شروع','time',True),f('end_time','ساعت پایان','time',True),f('days','روزهای هفته','days',default=['شنبه','یکشنبه','دوشنبه','سه‌شنبه','چهارشنبه']),f('driver_ids','رانندگان','multi-reference',source='drivers',default=[]),STATUS,NOTES
 ],['code','name','center_id','start_time','end_time','days','status'],'تعریف ساعت، روز و رانندگان شیفت؛ پشتیبانی از شیفت شب'),
 'missions': module('مأموریت‌ها','مأموریت','Flag',[
    CODE,f('name','عنوان مأموریت',required=True),ref('vehicle_id','موتورسیکلت','vehicles',True),ref('driver_id','راننده','drivers',True),ref('center_id','مرکز توزیع','centers',True),ref('shift_id','شیفت','shifts'),f('route','مسیر / منطقه'),f('category','دسته مأموریت'),num('load_kg','وزن بار (کیلوگرم)'),sel('status','وضعیت',[('planned','برنامه‌ریزی شده'),('active','در حال اجرا'),('completed','تکمیل شده'),('delayed','با تأخیر'),('failed','ناموفق'),('cancelled','لغو شده')],'planned'),f('started_at','زمان شروع','datetime-local'),f('due_at','مهلت تحویل','datetime-local'),f('ended_at','زمان پایان','datetime-local'),num('distance_km','مسافت (کیلومتر)',None),num('soc_start','شارژ آغاز (%)',None,0,100),num('soc_end','شارژ پایان (%)',None,0,100),f('result','نتیجه مأموریت','textarea'),NOTES
 ],['code','name','driver_id','vehicle_id','route','started_at','distance_km','status'],'تخصیص وسیله و راننده و ثبت نتیجه مأموریت'),
 'incidents': module('خرابی‌ها','خرابی','TriangleAlert',[
    CODE,f('title','عنوان خرابی',required=True),ref('vehicle_id','موتورسیکلت','vehicles',True),ref('battery_id','باتری','batteries'),sel('category','نوع خرابی',[('battery','باتری'),('bms','سیستم BMS'),('electrical','برق'),('mechanical','مکانیکی'),('charger','شارژر'),('other','سایر')],'mechanical'),sel('severity','شدت',SEVERITY,'high'),sel('status','وضعیت',[('open','باز'),('acknowledged','تأیید دریافت'),('repairing','در حال تعمیر'),('waiting','در انتظار قطعه'),('resolved','رفع شده'),('closed','بسته شده')],'open'),f('owner','مسئول رسیدگی',required=True),f('reported_at','زمان وقوع','datetime-local',True),f('responded_at','زمان پاسخ','datetime-local'),f('repair_started_at','شروع تعمیر','datetime-local'),f('resolved_at','رفع خرابی','datetime-local'),f('restored_at','بازگشت به سرویس','datetime-local'),f('root_cause','علت ریشه‌ای','textarea'),f('resolution','اقدام اصلاحی / شرط بازگشت','textarea'),num('cost','هزینه تعمیر (تومان)'),f('next_action','اقدام بعدی / تشدید'),NOTES
 ],['code','title','vehicle_id','severity','owner','reported_at','status'],'ثبت رخداد، تعمیر، زمان پاسخ و بازگشت به سرویس'),
 'tickets': module('پشتیبانی و SLA','درخواست پشتیبانی','Headset',[
    CODE,f('title','موضوع درخواست',required=True),ref('vehicle_id','موتورسیکلت','vehicles'),ref('incident_id','رخداد مرتبط','incidents'),ref('center_id','مرکز توزیع','centers',True),sel('priority','اولویت',SEVERITY,'high'),sel('status','وضعیت',[('open','باز'),('progress','در حال بررسی'),('waiting','در انتظار قطعه'),('answered','پاسخ داده شده'),('closed','بسته شده')],'open'),f('owner','کارشناس مسئول',required=True),f('reported_at','زمان ثبت','datetime-local',True),f('responded_at','زمان اولین پاسخ','datetime-local'),f('closed_at','زمان بسته شدن','datetime-local'),f('response','پاسخ / نتیجه','textarea'),f('escalation','ارجاع / تشدید'),NOTES
 ],['code','title','vehicle_id','priority','owner','reported_at','status'],'پیگیری درخواست‌ها و سنجش اهداف پاسخگویی'),
 'checks': module('کنترل پیش از شیفت','کنترل شیفت','ClipboardCheck',[
    CODE,ref('vehicle_id','موتورسیکلت','vehicles',True),ref('driver_id','راننده','drivers',True),ref('shift_id','شیفت','shifts'),f('checked_at','زمان کنترل','datetime-local',True),f('visual_ok','بازرسی ظاهری و ایمنی','checkbox',default=False),f('battery_ok','باتری و BMS بدون خطای بحرانی','checkbox',default=False),f('charger_ok','شارژر سازگار و سالم','checkbox',default=False),f('gps_ok','موقعیت‌یابی و دسترسی داده','checkbox',default=False),f('support_ok','پشتیبانی و گارانتی مشخص','checkbox',default=False),sel('status','نتیجه',[('pending','در انتظار بررسی'),('passed','تأیید شده'),('failed','رد شده')],'pending'),NOTES
 ],['code','vehicle_id','driver_id','checked_at','status'],'ثبت شواهد آمادگی پیش از تخصیص مأموریت'),
 'daily_logs': module('کارکرد روزانه','کارکرد روزانه','NotebookPen',[
    CODE,ref('vehicle_id','موتورسیکلت','vehicles',True),ref('shift_id','شیفت','shifts'),f('date','تاریخ','date',True),num('planned_minutes','زمان خدمت برنامه‌ریزی شده (دقیقه)',480,1,1440),num('available_minutes','زمان آماده‌به‌کاری (دقیقه)',0,0,1440),num('distance_km','پیمایش (کیلومتر)'),num('energy_kwh','انرژی (کیلووات‌ساعت)'),num('fuel_liters','بنزین مصرفی (لیتر)'),num('maintenance_cost','هزینه نگهداری (تومان)'),num('soc_end','شارژ پایان شیفت (%)',None,0,100),NOTES
 ],['code','vehicle_id','date','planned_minutes','available_minutes','distance_km','energy_kwh'],'خط مبنا و داده‌های لازم برای محاسبه آماده‌به‌کاری'),
 'gates': module('آمادگی پایلوت','دروازه تصمیم','ShieldCheck',[
    CODE,NAME,f('owner','مسئول',required=True),sel('status','وضعیت',[('open','باز'),('conditional','مشروط'),('approved','تأیید شده'),('rejected','رد شده')],'open'),f('evidence','شواهد / مرجع','textarea'),f('decision','تصمیم / اقدام بعدی','textarea'),f('reviewed_at','زمان بررسی','datetime-local'),NOTES
 ],['code','name','owner','status','reviewed_at'],'ثبت پنج پیش‌شرط و تصمیم ادامه، اصلاح یا توقف پایلوت'),
}

DEFAULT_SETTINGS = dict(organization='مپنا', low_soc=20, min_dispatch_soc=30, high_temperature=45, stale_hours=24, sla_critical_minutes=30, sla_high_minutes=120, sla_low_minutes=1440, sla_restore_hours=4, target_uptime=90, target_success=95, data_mode='empty')
ROLE_LABELS = {'admin':'مدیر سیستم','operator':'مدیر عملیات','technician':'پشتیبانی و تعمیرکار','charging':'اپراتور شارژ','viewer':'مشاهده‌گر'}
PERMISSIONS = {'admin': list(CATALOG), 'operator': ['missions','incidents','tickets','checks','daily_logs'], 'technician':['incidents','tickets','batteries'], 'charging':['charges','batteries'], 'viewer':[]}

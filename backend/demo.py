"""Explicitly labelled synthetic data. Never imported from operational evidence."""
from datetime import datetime, timedelta, timezone
from .catalog import CATALOG

def seed_demo(conn):
    from .app import validate_fields, store_record
    current=datetime.now(timezone.utc).replace(microsecond=0)
    def at(minutes=0,days=0):return (current+timedelta(minutes=minutes,days=days)).isoformat()
    def ident(kind,n):return f'demo-{kind}-{n}'
    def add(kind,n,**values):
        values.setdefault('code',f'{kind[:3].upper()}-{n:03}')
        if any(f['key']=='notes' for f in CATALOG[kind]['fields']):values.setdefault('notes','داده نمایشی برای بررسی امکانات نرم‌افزار؛ فاقد اعتبار عملیاتی.')
        data=validate_fields(conn,kind,values)
        store_record(conn,kind,ident(kind,n),data,True)
        return ident(kind,n)
    centers=[];fleets=[];drivers=[];batteries=[];vehicles=[];chargers=[]
    for n,(name,city,lat,lon) in enumerate([('تهران · مرکز شمال','تهران',35.75,51.41),('تهران · مرکز غرب','تهران',35.72,51.32),('کرج · مرکز البرز','کرج',35.83,50.99)],1):
        centers.append(add('centers',n,name=name,city=city,manager=['علی محمدی','سارا احمدی','رضا کریمی'][n-1],latitude=lat,longitude=lon,power_kw=22,safety_approved=True,status='active',address='مرکز توزیع نمونه'))
        fleets.append(add('fleets',n,name=['ناوگان پایلوت شمال','ناوگان توزیع غرب','ناوگان البرز'][n-1],center_id=centers[-1],owner='مپنا',service_owner='خدمات فنی مپنا',status='active'))
        chargers.append(add('chargers',n,name=f'ایستگاه شارژ {n}',center_id=centers[-1],power_kw=3.3,connector='سازگار با مدل نمونه',status='ready'))
    names=['علی رضایی','حسین احمدی','مهدی رضایی','سارا نادری','رضا کریمی','علی عباسی','امیر محمدی','نیما حسینی','محمد امینی','حمید قاسمی','آرش کاظمی','حامد اکبری']
    for i in range(12):
        n=i+1;c=i%3
        drivers.append(add('drivers',n,name=names[i],phone=f'0912000{n:04}',center_id=centers[c],trained=True,status='active'))
        b=None
        if n<=10:
            b=add('batteries',n,model='Li-ion 72V',center_id=centers[c],capacity_kwh=2.8,soc=[92,88,76,65,95,42,81,57,18,24][i],soh=98-i,temperature=27+i,cycles=65+7*i,status='critical' if n==10 else 'healthy',bms_critical=n==10,bms_error='BMS-E04' if n==10 else '',measured_at=at(-12))
            batteries.append(b)
        vehicles.append(add('vehicles',n,code=f'M-{n:03}',model='موتور برقی نمونه' if n<=10 else 'هوندا ۱۲۵',type='electric' if n<=10 else 'gasoline',plate=f'۱۲۳-۴۵{n:02}',vin=f'DEMOVIN{n:010}',fleet_id=fleets[c],driver_id=drivers[-1],battery_id=b,odometer=840+n*127,ownership='owned',purchase_date=(current-timedelta(days=35)).date().isoformat(),purchase_price=135000000 if n<=10 else 95000000,supplier='مپنا' if n<=10 else 'تأمین‌کننده نمونه',invoice=f'INV-{n:03}',support_owner='خدمات فنی مپنا',status='ready',safety_checked=True,charger_checked=True,data_checked=True,support_checked=True,last_location=['مرکز شمال تهران','مرکز غرب تهران','مرکز البرز'][c]))
    for n in range(1,4):add('shifts',n,name='شیفت صبح '+str(n),center_id=centers[n-1],start_time='08:00',end_time='16:00',driver_ids=[drivers[i] for i in range(12) if i%3==n-1],status='active')
    for n in range(1,10):add('checks',n,vehicle_id=vehicles[n-1],driver_id=drivers[n-1],checked_at=at(-150),visual_ok=True,battery_ok=True,charger_ok=True,gps_ok=True,support_ok=True,status='passed')
    for day in range(6,-1,-1):
        for i,v in enumerate(vehicles):
            n=(6-day)*12+i+1
            add('daily_logs',n,vehicle_id=v,date=(current-timedelta(days=day)).date().isoformat(),planned_minutes=480,available_minutes=410+(i*7+day*13)%65,distance_km=37+(i*9+day*11)%68,energy_kwh=2.1+(i*3+day)%10/10 if i<10 else 0,fuel_liters=0 if i<10 else 2.8,maintenance_cost=0)
        for k in range(5):
            n=(6-day)*5+k+1;i=(k+day)%8
            add('missions',n,name=['توزیع بسته‌های ونک','ارسال مرسوله‌های تجریش','توزیع محدوده آزادی','تحویل سفارش‌های گوهردشت','جمع‌آوری بسته‌ها'][k],vehicle_id=vehicles[i],driver_id=drivers[i],center_id=centers[i%3],status='completed' if n%11 else 'failed',started_at=at(-360-k*15,-day),ended_at=at(-220-k*10,-day),distance_km=18+k*7,soc_start=95,soc_end=68-k*4,result='تحویل ثبت شد' if n%11 else 'عدم حضور گیرنده',route=['ونک ← تجریش','آزادی ← صادقیه','کرج ← گوهردشت'][i%3])
    for n,i in [(36,1),(37,4)]:add('missions',n,name='توزیع مرسوله‌های شیفت جاری',vehicle_id=vehicles[i],driver_id=drivers[i],center_id=centers[i%3],status='active',started_at=at(-35),due_at=at(55),soc_start=90,route='مرکز غرب ← صادقیه')
    add('charges',1,vehicle_id=vehicles[8],charger_id=chargers[2],operator='اپراتور مرکز البرز',status='charging',started_at=at(-25),soc_start=18)
    for n in range(2,9):
        i=(n-2)%8
        add('charges',n,vehicle_id=vehicles[i],charger_id=chargers[i%3],operator='اپراتور شیفت صبح',status='completed',started_at=at(-500,-(n%5)),ended_at=at(-410,-(n%5)),soc_start=25,soc_end=95,energy_kwh=2.6)
    add('incidents',1,title='خطای بحرانی مدیریت باتری',vehicle_id=vehicles[9],battery_id=batteries[9],category='bms',severity='critical',status='repairing',owner='کارشناس فنی مپنا',reported_at=at(-85),responded_at=at(-65),repair_started_at=at(-55),next_action='بررسی BMS و تست ایمنی')
    add('incidents',2,title='بازرسی دوره‌ای ترمز',vehicle_id=vehicles[11],category='mechanical',severity='high',status='open',owner='رضا کریمی',reported_at=at(-45),next_action='بازرسی و تنظیم ترمز')
    add('incidents',3,title='اصلاح اتصال شارژ',vehicle_id=vehicles[0],category='charger',severity='high',status='closed',owner='کارشناس فنی مپنا',reported_at=at(-380,-1),responded_at=at(-360,-1),repair_started_at=at(-350,-1),resolved_at=at(-300,-1),restored_at=at(-290,-1),resolution='تعویض اتصال و تأیید تست شارژ',root_cause='اتصال نامناسب',cost=350000)
    for n,(title,i,priority,status) in enumerate([('بررسی خطای BMS',9,'critical','progress'),('سرویس دوره‌ای ترمز',11,'high','open'),('درخواست آموزش شارژ',2,'low','answered')],1):
        add('tickets',n,title=title,vehicle_id=vehicles[i],center_id=centers[i%3],priority=priority,status=status,owner=['مهدی رضایی','رضا کریمی','سارا نادری'][n-1],reported_at=at(-85 if n==1 else -40),responded_at=at(-65) if n==1 else at(-20) if n==3 else None,response='راهنمای استفاده ارائه شد' if n==3 else '')
    for n,name in enumerate(['ایمنی و برق مرکز توزیع','تناسب موتور با الگوی مأموریت','گارانتی و روش مجاز شارژ','دسترسی داده BMS','خدمات، قطعات و بازگشت به سرویس'],1):
        add('gates',n,name=name,owner='مپنا',status='open',decision='نیازمند شواهد واقعی پیش از تصمیم اجرایی')

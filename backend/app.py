from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import math
import os
from pathlib import Path
import re
import secrets
import sqlite3
import tempfile
import time
import threading
from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from .catalog import CATALOG, DEFAULT_SETTINGS, PERMISSIONS, ROLE_LABELS
from . import storage

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get('FLEET_DB', str(ROOT / 'data' / 'fleet.sqlite3')))
HASHER = PasswordHasher()
COOKIE = 'mahax_session'
CLOSED = {'resolved','closed'}
ACTIVE_MISSIONS = {'active','delayed'}
LOCAL_TZ = timezone(timedelta(hours=3, minutes=30))
INITIALIZE_LOCK = threading.Lock()

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def parse_dt(value):
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=LOCAL_TZ) if dt.tzinfo is None else dt

def fail(message, code=422):
    raise HTTPException(code, message)

@contextmanager
def database(write=False):
    conn = storage.connect(DB_PATH)
    try:
        conn.execute('PRAGMA foreign_keys=ON')
        if write:
            conn.execute('BEGIN IMMEDIATE')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def records(conn, kind):
    return [dict(json.loads(r['data']),id=r['id'],created_at=r['created_at'],updated_at=r['updated_at'],demo=bool(r['demo'])) for r in conn.execute('SELECT * FROM records WHERE kind=? ORDER BY created_at DESC,id DESC',(kind,))]

def get_record(conn, kind, id):
    row = conn.execute('SELECT * FROM records WHERE kind=? AND id=?',(kind,id)).fetchone()
    if not row:
        fail('رکورد مرتبط پیدا نشد.',404)
    return dict(json.loads(row['data']), id=row['id'],created_at=row['created_at'],updated_at=row['updated_at'],demo=bool(row['demo']))

def settings(conn):
    return {**DEFAULT_SETTINGS, **json.loads(conn.execute('SELECT data FROM settings WHERE id=1').fetchone()[0])}

def audit(conn,user,action,kind='',rid='',detail=''):
    conn.execute('INSERT INTO audit(at,username,action,kind,record_id,detail) VALUES(?,?,?,?,?,?)',(now(),user['username'],action,kind,rid,detail))

def initialize():
    remote = bool(storage.remote_url())
    if not remote and not storage.is_hosted():
        DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    with database() as conn:
        if not remote:
            conn.execute('PRAGMA journal_mode=WAL')
        schema = '''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,kind TEXT NOT NULL,code TEXT NOT NULL,data TEXT NOT NULL CHECK(json_valid(data)),demo INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(kind,code));
        CREATE INDEX IF NOT EXISTS idx_records_kind ON records(kind);
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT NOT NULL,username TEXT NOT NULL,action TEXT NOT NULL,kind TEXT,record_id TEXT,detail TEXT);
        CREATE TABLE IF NOT EXISTS login_attempts(key TEXT PRIMARY KEY,failures INTEGER NOT NULL,blocked_until REAL NOT NULL);
        '''
        # Explicit transaction also prevents concurrent cold starts from
        # generating competing administrator accounts in the hosted database.
        conn.execute('BEGIN IMMEDIATE')
        for statement in schema.split(';'):
            if statement.strip():
                conn.execute(statement)
        conn.execute('INSERT OR IGNORE INTO settings VALUES(1,?)',(json.dumps(DEFAULT_SETTINGS),))
        # Rebrand only the shipped organization name; preserve customized settings.
        stored_settings = json.loads(conn.execute('SELECT data FROM settings WHERE id=1').fetchone()[0])
        if stored_settings.get('organization') == 'ماهکس × توسن':
            stored_settings['organization'] = DEFAULT_SETTINGS['organization']
            conn.execute('UPDATE settings SET data=? WHERE id=1',(json.dumps(stored_settings),))
        if not conn.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            if remote and not os.environ.get('FLEET_ADMIN_PASSWORD'):
                raise storage.StorageConfigurationError('FLEET_ADMIN_PASSWORD is required for the first hosted administrator')
            password = os.environ.get('FLEET_ADMIN_PASSWORD') or secrets.token_urlsafe(14)
            if len(password)<10:
                raise RuntimeError('FLEET_ADMIN_PASSWORD must contain at least 10 characters')
            conn.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?)',(secrets.token_hex(8),'admin','مدیر سیستم',HASHER.hash(password),'admin',1,now()))
            if not remote and not os.environ.get('FLEET_ADMIN_PASSWORD'):
                (DB_PATH.parent/'initial-credentials.txt').write_text(f'URL: http://127.0.0.1:8000\nUsername: admin\nPassword: {password}\nChange the password after first login.\n',encoding='utf-8')

@asynccontextmanager
async def lifespan(app):
    # Local execution remains eager. Serverless runtimes can omit ASGI
    # lifespan; the middleware below initializes safely on the first request.
    if not storage.is_hosted():
        initialize()
        app.state.database_ready = True
    yield
    app.state.database_ready = False

def allowed_hosts():
    hosts = {'localhost', '127.0.0.1', 'testserver'}
    for variable in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL', 'VERCEL_BRANCH_URL', 'FLEET_ALLOWED_HOSTS'):
        for value in os.environ.get(variable, '').split(','):
            value = value.strip()
            if value:
                host = urlsplit(value if '://' in value else 'https://' + value).hostname
                if host:
                    hosts.add(host)
    return sorted(hosts)


def ensure_ready():
    with INITIALIZE_LOCK:
        if not app.state.database_ready:
            initialize()
            app.state.database_ready = True


app=FastAPI(title='MAPNA Fleet API',version='1.1.0',lifespan=lifespan,docs_url=None,redoc_url=None)
app.state.database_ready = False

@app.middleware('http')
async def headers_and_origin(request,call_next):
    if request.url.hostname not in allowed_hosts():
        return JSONResponse({'detail':'دامنهٔ درخواست مجاز نیست.'},400)
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        origin=request.headers.get('origin')
        # The Vercel proxy can speak HTTP internally; the browser uses HTTPS.
        origins = {str(request.base_url).rstrip('/')}
        if storage.is_hosted():
            origins = {'https://' + request.headers['host']}
        else:
            origins.update({'http://127.0.0.1:5173', 'http://localhost:5173'})
        if origin and origin not in origins:
            return JSONResponse({'detail':'مبدأ درخواست مجاز نیست.'},403)
    if request.url.path.startswith('/api') and not app.state.database_ready:
        try:
            await run_in_threadpool(ensure_ready)
        except storage.StorageConfigurationError as error:
            logging.getLogger(__name__).error('Database configuration: %s', error)
            return JSONResponse({'detail':'تنظیمات پایگاه‌دادهٔ آنلاین کامل نیست. مدیر سایت باید اتصال پایگاه‌داده و رمز اولیهٔ مدیر را در Vercel تنظیم و دوباره منتشر کند.'},503,headers={'Cache-Control':'no-store'})
        except Exception as error:
            # Do not expose connection URLs, tokens, or driver exception text.
            logging.getLogger(__name__).error('Database initialization failed (%s)', type(error).__name__)
            return JSONResponse({'detail':'اتصال به پایگاه‌داده برقرار نشد. مدیر سایت باید اتصال و دسترسی پایگاه‌داده را بررسی کند.'},503,headers={'Cache-Control':'no-store'})
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if request.url.path.startswith('/api'):
        response.headers['Cache-Control']='no-store'
    return response

def current_user(request:Request):
    raw=request.cookies.get(COOKIE,'')
    with database() as conn:
        row=conn.execute('SELECT u.id,u.username,u.name,u.role,u.active,s.csrf,s.token_hash FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?',(hashlib.sha256(raw.encode()).hexdigest(),time.time())).fetchone()
    if not row or not row['active']:
        fail('لطفاً وارد حساب کاربری شوید.',401)
    if request.method in {'POST','PUT','PATCH','DELETE'} and not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),row['csrf']):
        fail('نشست معتبر نیست؛ صفحه را تازه‌سازی کنید.',403)
    return dict(row)

def admin(user=Depends(current_user)):
    if user['role']!='admin':
        fail('این عملیات فقط برای مدیر سیستم مجاز است.',403)
    return user

def permit(user,kind):
    if kind not in CATALOG:
        fail('بخش موردنظر وجود ندارد.',404)
    if kind not in PERMISSIONS.get(user['role'],[]):
        fail('برای ویرایش این بخش دسترسی ندارید.',403)

def public_user(user):
    return {k:user[k] for k in ['id','username','name','role']}

class Login(BaseModel):
    username:str=Field(min_length=1,max_length=80)
    password:str=Field(min_length=1,max_length=256)

@app.get('/api/health')
def health():
    try:
        with database() as conn:
            conn.execute('SELECT 1 FROM settings WHERE id=1').fetchone()
        return {'status':'ok','database':'connected','storage':'turso' if storage.remote_url() else 'sqlite'}
    except Exception:
        return JSONResponse({'status':'error','database':'unavailable'},503,headers={'Cache-Control':'no-store'})

@app.post('/api/auth/login')
def login(payload:Login,request:Request,response:Response):
    key=(request.client.host if request.client else 'local')+':'+payload.username.casefold()
    with database(True) as conn:
        attempt=conn.execute('SELECT * FROM login_attempts WHERE key=?',(key,)).fetchone()
        if attempt and attempt['blocked_until']>time.time():
            fail('تلاش‌های ناموفق زیاد است. چند دقیقه بعد دوباره امتحان کنید.',429)
        user=conn.execute('SELECT * FROM users WHERE username=? AND active=1',(payload.username,)).fetchone()
        valid=False
        try:
            valid=bool(user and HASHER.verify(user['password_hash'],payload.password))
        except (VerifyMismatchError,InvalidHashError):
            pass
        if not valid:
            count=(attempt['failures'] if attempt and attempt['blocked_until']>time.time()-900 else 0)+1
            conn.execute('INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)',(key,count,time.time()+900 if count>=5 else time.time()))
            conn.commit()
            fail('نام کاربری یا رمز عبور صحیح نیست.',401)
        conn.execute('DELETE FROM login_attempts WHERE key=?',(key,))
        conn.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
        token=secrets.token_urlsafe(32)
        csrf=secrets.token_urlsafe(24)
        conn.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf,time.time()+43200))
        audit(conn,user,'login')
    response.set_cookie(COOKIE,token,httponly=True,samesite='strict',secure=storage.is_hosted() or os.environ.get('FLEET_HTTPS')=='1',max_age=43200,path='/')
    return {'user':public_user(user),'csrf':csrf}

@app.get('/api/auth/me')
def me(user=Depends(current_user)):
    return {'user':public_user(user),'csrf':user['csrf']}

@app.post('/api/auth/logout')
def logout(response:Response,user=Depends(current_user)):
    with database(True) as conn:
        conn.execute('DELETE FROM sessions WHERE token_hash=?',(user['token_hash'],))
        audit(conn,user,'logout')
    response.delete_cookie(COOKIE,path='/')
    return {'ok':True}

class PasswordChange(BaseModel):
    current_password:str=Field(max_length=256)
    new_password:str=Field(min_length=10,max_length=256)

@app.post('/api/auth/password')
def password_change(payload:PasswordChange,user=Depends(current_user)):
    with database(True) as conn:
        row=conn.execute('SELECT password_hash FROM users WHERE id=?',(user['id'],)).fetchone()
        try:
            HASHER.verify(row[0],payload.current_password)
        except VerifyMismatchError:
            fail('رمز عبور فعلی صحیح نیست.',400)
        conn.execute('UPDATE users SET password_hash=? WHERE id=?',(HASHER.hash(payload.new_password),user['id']))
        conn.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(user['id'],user['token_hash']))
        audit(conn,user,'password_change')
    return {'ok':True}

def validate_fields(conn,kind,data):
    if kind not in CATALOG:
        fail('بخش موردنظر وجود ندارد.',404)
    fields=CATALOG[kind]['fields']
    extra=set(data)-{f['key'] for f in fields}
    if extra:
        fail('فیلد ناشناخته: '+', '.join(sorted(extra)))
    clean={}
    for field in fields:
        key=field['key']; value=data.get(key,field.get('default')); label=field['label']; typ=field['type']
        if value=='' or value is None:
            if field.get('required'):
                fail(f'«{label}» الزامی است.')
            clean[key]=None if typ in ['number','reference','datetime-local','date','time'] else ''
            if typ=='checkbox':clean[key]=False
            if typ in ['days','multi-reference']:clean[key]=[]
            continue
        if typ=='number':
            if isinstance(value,bool):fail(f'«{label}» باید عدد باشد.')
            try:value=float(value)
            except (ValueError,TypeError):fail(f'«{label}» باید عدد باشد.')
            if not math.isfinite(value) or not field.get('min',0)<=value<=field.get('max',1e12):
                fail(f'«{label}» خارج از محدوده مجاز است.')
        elif typ=='checkbox':
            if not isinstance(value,bool):fail(f'«{label}» باید بله یا خیر باشد.')
        elif typ in ['days','multi-reference']:
            if not isinstance(value,list) or len(value)>100:fail(f'«{label}» معتبر نیست.')
            if typ=='multi-reference':
                for id in value:get_record(conn,field['source'],id)
            elif any(d not in ['شنبه','یکشنبه','دوشنبه','سه‌شنبه','چهارشنبه','پنجشنبه','جمعه'] for d in value):
                fail('روز هفته نامعتبر است.')
        else:
            if not isinstance(value,str):fail(f'«{label}» باید متن باشد.')
            value=value.strip()
            if len(value)>4000 or (field.get('required') and not value):fail(f'«{label}» معتبر نیست.')
            if typ=='select' and value not in {o['value'] for o in field['options']}:fail(f'«{label}» معتبر نیست.')
            if typ=='reference':get_record(conn,field['source'],value)
            if typ in ['date','datetime-local','time']:
                try:
                    if typ=='date':datetime.strptime(value,'%Y-%m-%d')
                    elif typ=='time':datetime.strptime(value,'%H:%M')
                    else:parse_dt(value)
                except (ValueError,TypeError):fail(f'«{label}» تاریخ یا ساعت معتبر نیست.')
        clean[key]=value
    return clean

def store_record(conn,kind,rid,data,demo=False):
    stamp=now()
    try:
        conn.execute('INSERT INTO records(id,kind,code,data,demo,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET code=excluded.code,data=excluded.data,updated_at=excluded.updated_at', (rid,kind,data['code'],json.dumps(data,ensure_ascii=False),demo,stamp,stamp))
    except sqlite3.IntegrityError:
        fail('این شناسه قبلاً ثبت شده است.',409)

def raw_update(conn,kind,rid,changes):
    row=get_record(conn,kind,rid)
    data={f['key']:row.get(f['key']) for f in CATALOG[kind]['fields']}
    data.update(changes)
    store_record(conn,kind,rid,data,row['demo'])

def vehicle_readiness(conn,vehicle,exclude=None):
    cfg=settings(conn); reasons=[]
    if vehicle['status']!='ready':reasons.append('وضعیت پایه موتور آماده نیست')
    for key,label in [('safety_checked','بازرسی ایمنی'),('data_checked','دسترسی داده'),('support_checked','پشتیبانی')]:
        if not vehicle.get(key):reasons.append(label+' تأیید نشده')
    fleet=get_record(conn,'fleets',vehicle['fleet_id'])
    center=get_record(conn,'centers',fleet['center_id'])
    if fleet['status']!='active' or center['status']!='active':reasons.append('ناوگان یا مرکز غیرفعال است')
    if not center.get('safety_approved'):reasons.append('ایمنی مرکز تأیید نشده')
    if vehicle['type']=='electric':
        if not vehicle.get('charger_checked'):reasons.append('سازگاری شارژر تأیید نشده')
        if not vehicle.get('battery_id'):reasons.append('باتری تخصیص داده نشده')
        else:
            b=get_record(conn,'batteries',vehicle['battery_id'])
            if b['status']!='healthy' or b.get('bms_critical'):reasons.append('باتری یا BMS نیازمند رسیدگی است')
            if b.get('soc') is None or b['soc']<cfg['min_dispatch_soc']:reasons.append('شارژ کافی نیست')
            if b.get('temperature') is not None and b['temperature']>=cfg['high_temperature']:reasons.append('دمای باتری بالاست')
            if not b.get('measured_at') or (datetime.now(timezone.utc)-parse_dt(b['measured_at'])).total_seconds()>cfg['stale_hours']*3600:reasons.append('داده باتری تازه نیست')
    if any(i['vehicle_id']==vehicle['id'] and i['status'] not in CLOSED for i in records(conn,'incidents')):reasons.append('رخداد باز دارد')
    if any(c['id']!=exclude and c['vehicle_id']==vehicle['id'] and c['status']=='charging' for c in records(conn,'charges')):reasons.append('در حال شارژ است')
    if any(m['id']!=exclude and m['vehicle_id']==vehicle['id'] and m['status'] in ACTIVE_MISSIONS for m in records(conn,'missions')):reasons.append('مأموریت فعال دارد')
    return reasons

def business_rules(conn,kind,data,rid,old=None):
    def required(*keys):
        for key in keys:
            if data.get(key) is None or data.get(key)=='':fail('برای این وضعیت، '+next(f['label'] for f in CATALOG[kind]['fields'] if f['key']==key)+' الزامی است.')
    def ordered(*keys,allow_future=False):
        dates=[parse_dt(data[k]) for k in keys if data.get(k)]
        if dates!=sorted(dates):fail('ترتیب زمانی شروع، پاسخ و پایان صحیح نیست.')
        if not allow_future and any(dt>datetime.now(timezone.utc)+timedelta(minutes=5) for dt in dates):fail('زمان رویداد ثبت‌شده نمی‌تواند در آینده باشد.')
    if kind=='batteries':ordered('measured_at')
    if kind=='vehicles':
        if old and any(x['vehicle_id']==rid and x['status'] in ACTIVE_MISSIONS for x in records(conn,'missions')):
            if any(data.get(k)!=old.get(k) for k in ['battery_id','fleet_id','type']):fail('هنگام مأموریت فعال، باتری، نوع یا ناوگان موتور قابل تغییر نیست.',409)
        if old and any(x['vehicle_id']==rid and x['status']=='charging' for x in records(conn,'charges')):
            if any(data.get(k)!=old.get(k) for k in ['battery_id','fleet_id','type']):fail('هنگام شارژ، مشخصات اتصال موتور قابل تغییر نیست.',409)
        if data['type']=='gasoline' and data.get('battery_id'):fail('باتری ناوگان برقی به موتور بنزینی تخصیص نمی‌یابد.')
        for key in ['plate','vin','battery_id']:
            if data.get(key) and any(v['id']!=rid and v.get(key)==data[key] for v in records(conn,'vehicles')):fail('پلاک، شاسی یا باتری تکراری است.',409)
        fleet=get_record(conn,'fleets',data['fleet_id'])
        if data.get('battery_id') and get_record(conn,'batteries',data['battery_id'])['center_id']!=fleet['center_id']:fail('مرکز باتری و ناوگان باید یکسان باشد.')
    if kind=='batteries' and old and data['center_id']!=old['center_id']:
        if any(v.get('battery_id')==rid for v in records(conn,'vehicles')):fail('ابتدا تخصیص باتری به موتور را بردارید.',409)
    if kind=='fleets' and old and data['center_id']!=old['center_id']:
        if any(v['fleet_id']==rid for v in records(conn,'vehicles')):fail('مرکز ناوگان دارای موتور قابل تغییر نیست.',409)
    if kind=='chargers' and old and data['center_id']!=old['center_id']:
        if any(c['charger_id']==rid and c['status']=='charging' for c in records(conn,'charges')):fail('هنگام شارژ فعال، مرکز شارژر قابل تغییر نیست.',409)
    if kind=='missions':
        ordered('started_at','ended_at',allow_future=data['status']=='planned')
        if old and old['status'] in ['completed','failed','cancelled'] and any(data.get(k)!=old.get(k) for k in ['vehicle_id','driver_id','distance_km','soc_end','status']):fail('مأموریت پایان‌یافته قابل بازگشایی یا تغییر کارکرد نیست.',409)
        v=get_record(conn,'vehicles',data['vehicle_id']); driver=get_record(conn,'drivers',data['driver_id'])
        if data['status'] in ACTIVE_MISSIONS:
            required('started_at')
            if data.get('ended_at'):fail('مأموریت فعال نباید زمان پایان داشته باشد.')
            reasons=vehicle_readiness(conn,v,rid)
            if reasons:fail('تخصیص مجاز نیست: '+'، '.join(reasons),409)
            if driver['status']!='active' or not driver.get('trained'):fail('راننده باید فعال و آموزش‌دیده باشد.',409)
            if driver['center_id']!=data['center_id'] or get_record(conn,'fleets',v['fleet_id'])['center_id']!=data['center_id']:fail('مرکز موتور، راننده و مأموریت باید یکسان باشد.')
            if data.get('shift_id'):
                shift=get_record(conn,'shifts',data['shift_id'])
                if shift['status']!='active' or shift['center_id']!=data['center_id'] or data['driver_id'] not in shift['driver_ids']:fail('شیفت باید فعال، متعلق به همین مرکز و شامل راننده مأموریت باشد.')
            if any(m['id']!=rid and m['driver_id']==data['driver_id'] and m['status'] in ACTIVE_MISSIONS for m in records(conn,'missions')):fail('راننده مأموریت فعال دیگری دارد.',409)
        if old and old['status'] in ACTIVE_MISSIONS and any(data.get(k)!=old.get(k) for k in ['vehicle_id','driver_id']):fail('ابتدا مأموریت فعال را پایان دهید؛ سپس تخصیص جدید ایجاد کنید.',409)
        if data['status'] in ['completed','failed']:
            required('started_at','ended_at','distance_km','result')
            if v['type']=='electric':required('soc_start','soc_end')
    if kind=='charges':
        ordered('started_at','ended_at')
        v=get_record(conn,'vehicles',data['vehicle_id']); charger=get_record(conn,'chargers',data['charger_id'])
        if v['type']!='electric' or not v.get('battery_id'):fail('شارژ فقط برای موتور برقی دارای باتری امکان‌پذیر است.')
        if old and old['status'] in ['completed','failed','cancelled'] and any(data.get(k)!=old.get(k) for k in ['vehicle_id','charger_id','soc_end','energy_kwh','status']):fail('نوبت پایان‌یافته قابل بازگشایی یا تغییر مقادیر نهایی نیست.',409)
        if old and old['status']=='charging' and any(data.get(k)!=old.get(k) for k in ['vehicle_id','charger_id']):fail('ابتدا نوبت شارژ فعال را پایان دهید.',409)
        if data['status']=='charging':
            required('started_at','soc_start')
            if data.get('ended_at'):fail('نوبت در حال شارژ نباید زمان پایان داشته باشد.')
            if charger['status']!='ready':fail('شارژر آماده نیست.',409)
            b=get_record(conn,'batteries',v['battery_id'])
            if b['status']!='healthy' or b.get('bms_critical'):fail('باتری معیوب برای شارژ مجاز نیست.',409)
            if b.get('temperature') is not None and b['temperature']>=settings(conn)['high_temperature']:fail('دمای باتری برای شروع شارژ مجاز نیست.',409)
            if not v.get('charger_checked'):fail('سازگاری شارژر و وسیله تأیید نشده است.',409)
            if any(i['vehicle_id']==v['id'] and i['status'] not in CLOSED for i in records(conn,'incidents')):fail('وسیله دارای رخداد باز برای شارژ مجاز نیست.',409)
            if charger['center_id']!=get_record(conn,'fleets',v['fleet_id'])['center_id']:fail('مرکز شارژر و موتور باید یکسان باشد.')
            if any(x['id']!=rid and x['status']=='charging' and (x['vehicle_id']==data['vehicle_id'] or x['charger_id']==data['charger_id']) for x in records(conn,'charges')):fail('موتور یا شارژر هم‌اکنون در نوبت دیگری فعال است.',409)
            if any(x['vehicle_id']==v['id'] and x['status'] in ACTIVE_MISSIONS for x in records(conn,'missions')):fail('موتور مأموریت فعال دارد.',409)
        if data['status']=='completed':
            required('started_at','ended_at','soc_start','soc_end','energy_kwh')
            if data['soc_end']<data['soc_start']:fail('شارژ نهایی نباید کمتر از شارژ اولیه باشد.')
        if data['status']=='failed':required('error_code','ended_at')
    if kind=='incidents':
        ordered('reported_at','responded_at','repair_started_at','resolved_at','restored_at')
        if data['status'] in CLOSED:required('responded_at','resolved_at','restored_at','resolution')
        if data.get('battery_id') and get_record(conn,'vehicles',data['vehicle_id']).get('battery_id')!=data['battery_id']:fail('باتری انتخاب‌شده به این موتور تخصیص ندارد.')
    if kind=='tickets':
        ordered('reported_at','responded_at','closed_at')
        if data['status'] in ['answered','closed']:required('responded_at','response')
        if data['status']=='closed':required('closed_at')
    if kind=='checks' and data['status']=='passed':
        if not all(data[k] for k in ['visual_ok','battery_ok','charger_ok','gps_ok','support_ok']):fail('تمام کنترل‌های پیش از شیفت باید تأیید شوند.')
        ordered('checked_at')
    if kind=='daily_logs':
        if data['available_minutes']>data['planned_minutes']:fail('زمان آماده‌به‌کاری نباید بیشتر از زمان برنامه‌ریزی شده باشد.')
        if any(x['id']!=rid and x['vehicle_id']==data['vehicle_id'] and x['date']==data['date'] and x.get('shift_id')==data.get('shift_id') for x in records(conn,'daily_logs')):fail('کارکرد این موتور، تاریخ و شیفت قبلاً ثبت شده است.',409)
    if kind=='gates' and data['status']=='approved':required('evidence','reviewed_at')

def save(conn,kind,data,user,rid=None,demo=False):
    old=get_record(conn,kind,rid) if rid else None
    rid=rid or secrets.token_hex(8)
    cleaned=validate_fields(conn,kind,data)
    business_rules(conn,kind,cleaned,rid,old)
    store_record(conn,kind,rid,cleaned,demo)
    if kind=='incidents' and cleaned['status'] not in CLOSED:
        for charge in records(conn,'charges'):
            if charge['vehicle_id']==cleaned['vehicle_id'] and charge['status']=='charging':
                raw_update(conn,'charges',charge['id'],{'status':'failed','ended_at':now(),'error_code':'INCIDENT:'+cleaned['code']})
                audit(conn,user,'charge_interrupted','charges',charge['id'],cleaned['code'])
    if kind=='missions' and cleaned['status'] in ['completed','failed'] and (not old or old['status'] not in ['completed','failed']):
        v=get_record(conn,'vehicles',cleaned['vehicle_id'])
        raw_update(conn,'vehicles',v['id'],{'odometer':v['odometer']+cleaned['distance_km']})
        if v.get('battery_id') and cleaned.get('soc_end') is not None:
            b=get_record(conn,'batteries',v['battery_id'])
            if not b.get('measured_at') or parse_dt(cleaned['ended_at'])>=parse_dt(b['measured_at']):raw_update(conn,'batteries',v['battery_id'],{'soc':cleaned['soc_end'],'measured_at':cleaned['ended_at']})
    if kind=='charges' and cleaned['status']=='completed' and (not old or old['status']!='completed'):
        v=get_record(conn,'vehicles',cleaned['vehicle_id']); b=get_record(conn,'batteries',v['battery_id'])
        changes={'cycles':b['cycles']+1}
        if not b.get('measured_at') or parse_dt(cleaned['ended_at'])>=parse_dt(b['measured_at']):changes.update(soc=cleaned['soc_end'],measured_at=cleaned['ended_at'])
        raw_update(conn,'batteries',b['id'],changes)
    if kind=='checks' and cleaned['status']=='passed':
        raw_update(conn,'vehicles',cleaned['vehicle_id'],{'safety_checked':True,'charger_checked':True,'data_checked':True,'support_checked':True})
    audit(conn,user,'update' if old else 'create',kind,rid,cleaned['code'])
    return get_record(conn,kind,rid)

def all_data(conn):
    data={kind:records(conn,kind) for kind in CATALOG}
    for v in data['vehicles']:
        reasons=vehicle_readiness(conn,v)
        v['readiness_reasons']=reasons
        if any(i['vehicle_id']==v['id'] and i['status'] not in CLOSED for i in data['incidents']):effective='out'
        elif any(c['vehicle_id']==v['id'] and c['status']=='charging' for c in data['charges']):effective='charging'
        elif any(m['vehicle_id']==v['id'] and m['status'] in ACTIVE_MISSIONS for m in data['missions']):effective='mission'
        elif reasons:effective='maintenance' if v['status']=='maintenance' else 'out'
        else:effective='ready'
        v['effective_status']=effective
    return data

@app.get('/api/bootstrap')
def bootstrap(user=Depends(current_user)):
    with database() as conn:
        data=all_data(conn); cfg=settings(conn)
        count=conn.execute('SELECT COUNT(*) FROM records WHERE demo=1').fetchone()[0]
        return {'catalog':CATALOG,'records':data,'settings':cfg,'permissions':PERMISSIONS[user['role']],'roles':ROLE_LABELS,'demo_count':count,'server_time':now()}

@app.post('/api/records/{kind}')
def create(kind:str,payload:dict[str,Any],user=Depends(current_user)):
    permit(user,kind)
    with database(True) as conn:return save(conn,kind,payload,user)

@app.put('/api/records/{kind}/{rid}')
def update(kind:str,rid:str,payload:dict[str,Any],user=Depends(current_user)):
    permit(user,kind)
    with database(True) as conn:return save(conn,kind,payload,user,rid)

@app.delete('/api/records/{kind}/{rid}')
def delete(kind:str,rid:str,user=Depends(admin)):
    if kind not in CATALOG:fail('بخش یافت نشد.',404)
    with database(True) as conn:
        row=get_record(conn,kind,rid)
        if kind in ['charges','missions'] and row['status'] not in ['planned','queued','cancelled']:fail('سوابق عملیاتی قابل حذف نیستند؛ برای اصلاح، توضیح ثبت کنید.',409)
        if kind=='incidents' and row['status'] not in CLOSED:fail('ابتدا رخداد را با ثبت نتیجه ببندید.',409)
        for other,meta in CATALOG.items():
            refs=[f for f in meta['fields'] if f.get('source')==kind]
            if refs:
                for record in records(conn,other):
                    if any(record.get(f['key'])==rid or isinstance(record.get(f['key']),list) and rid in record[f['key']] for f in refs):fail('رکورد در '+meta['label']+' استفاده شده است. ابتدا ارتباط را اصلاح کنید.',409)
        conn.execute('DELETE FROM records WHERE id=?',(rid,));audit(conn,user,'delete',kind,rid,row['code'])
    return {'ok':True}

@app.get('/api/audit')
def audit_log(user=Depends(admin)):
    with database() as conn:return [dict(r) for r in conn.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 250')]

@app.put('/api/settings')
def update_settings(payload:dict[str,Any],user=Depends(admin)):
    with database(True) as conn:
        cfg=settings(conn)
        if set(payload)-set(DEFAULT_SETTINGS) or 'data_mode' in payload:fail('تنظیمات ناشناخته است.')
        for key,value in payload.items():
            if key=='organization':
                if not isinstance(value,str) or not 1<=len(value.strip())<=100:fail('نام سازمان معتبر نیست.')
            else:
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<value<=100000:fail('آستانه باید عدد مثبت باشد.')
                if key in ['low_soc','min_dispatch_soc','target_uptime','target_success'] and value>100:fail('درصد باید حداکثر ۱۰۰ باشد.')
            cfg[key]=value
        if cfg['low_soc']>cfg['min_dispatch_soc']:fail('حداقل شارژ مأموریت باید دست‌کم برابر آستانه هشدار باشد.')
        conn.execute('UPDATE settings SET data=? WHERE id=1',(json.dumps(cfg),));audit(conn,user,'settings_update')
    return cfg

class UserInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    username:str=Field(min_length=3,max_length=50,pattern=r'^[A-Za-z0-9_.-]+$')
    name:str=Field(min_length=1,max_length=100)
    role:str
    password:str|None=Field(default=None,min_length=10,max_length=256)
    active:bool=True

@app.get('/api/users')
def users_list(user=Depends(admin)):
    with database() as conn:return [dict(r) for r in conn.execute('SELECT id,username,name,role,active,created_at FROM users ORDER BY created_at')]

def save_user(conn,payload,user,uid=None):
    editing=bool(uid)
    if payload.role not in ROLE_LABELS:fail('نقش نامعتبر است.')
    if uid:
        old=conn.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        if not old:fail('کاربر پیدا نشد.',404)
        if uid==user['id'] and (not payload.active or payload.role!='admin'):fail('تغییر نقش یا غیرفعال کردن حساب خودتان مجاز نیست.')
    elif not payload.password:fail('رمز عبور الزامی است.')
    try:
        if uid:
            conn.execute('UPDATE users SET username=?,name=?,role=?,active=? WHERE id=?',(payload.username,payload.name,payload.role,payload.active,uid))
            if payload.password:conn.execute('UPDATE users SET password_hash=? WHERE id=?',(HASHER.hash(payload.password),uid))
            conn.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(uid,user['token_hash']))
        else:
            uid=secrets.token_hex(8)
            conn.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?)',(uid,payload.username,payload.name,HASHER.hash(payload.password),payload.role,payload.active,now()))
    except sqlite3.IntegrityError:fail('نام کاربری تکراری است.',409)
    audit(conn,user,'user_update' if editing else 'user_create','users',uid,payload.username)
    return {'id':uid}

@app.post('/api/users')
def user_create(payload:UserInput,user=Depends(admin)):
    with database(True) as conn:return save_user(conn,payload,user)

@app.put('/api/users/{uid}')
def user_update(uid:str,payload:UserInput,user=Depends(admin)):
    with database(True) as conn:return save_user(conn,payload,user,uid)

def csv_safe(value):
    if value is None:return ''
    text=json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@','\t','\r')) else text

@app.get('/api/export/{kind}')
def export_csv(kind:str,template:bool=False,user=Depends(current_user)):
    if kind not in CATALOG:fail('بخش یافت نشد.',404)
    output=io.StringIO(newline=''); writer=csv.writer(output); fields=CATALOG[kind]['fields']
    writer.writerow([f['key'] for f in fields])
    if not template:
        with database() as conn:
            for row in reversed(records(conn,kind)):
                vals=[]
                for field in fields:
                    value=row.get(field['key'])
                    if field['type']=='reference' and value:value=get_record(conn,field['source'],value)['code']
                    if field['type']=='multi-reference' and value:value=[get_record(conn,field['source'],v)['code'] for v in value]
                    vals.append(csv_safe(value))
                writer.writerow(vals)
    return Response('\ufeff'+output.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="{kind}{"-template" if template else ""}.csv"'})

class ImportData(BaseModel):
    content:str=Field(max_length=2_000_000)

@app.post('/api/import/{kind}')
def import_csv(kind:str,payload:ImportData,user=Depends(admin)):
    if kind not in CATALOG:fail('بخش یافت نشد.',404)
    reader=csv.DictReader(io.StringIO(payload.content.lstrip('\ufeff')))
    if not reader.fieldnames or 'code' not in reader.fieldnames:fail('فایل باید ستون code داشته باشد.')
    rows=list(reader)
    if not rows or len(rows)>1000:fail('فایل باید بین ۱ تا ۱۰۰۰ ردیف داشته باشد.')
    with database(True) as conn:
        for i,row in enumerate(rows,2):
            if None in row:fail(f'ردیف {i}: تعداد ستون‌ها صحیح نیست.')
            data=dict(row)
            try:
                for field in CATALOG[kind]['fields']:
                    key=field['key']; value=data.get(key)
                    if value is None or value=='':continue
                    if field['type']=='checkbox':
                        if value.lower() not in ['true','false','1','0','بله','خیر']:fail('مقدار بولی نامعتبر است.')
                        data[key]=value.lower() in ['true','1','بله']
                    elif field['type'] in ['days','multi-reference']:data[key]=json.loads(value)
                    if field['type']=='reference':
                        match=next((r for r in records(conn,field['source']) if r['code']==value or r['id']==value),None)
                        if not match:fail('شناسه مرتبط پیدا نشد: '+value)
                        data[key]=match['id']
                    if field['type']=='multi-reference':
                        options=records(conn,field['source']); data[key]=[next((r['id'] for r in options if r['code']==v or r['id']==v),v) for v in data[key]]
                save(conn,kind,data,user)
            except (HTTPException,ValueError,TypeError) as e:fail(f'ردیف {i}: '+str(getattr(e,'detail',e)))
        audit(conn,user,'csv_import',kind,detail=str(len(rows)))
    return {'imported':len(rows)}

@app.get('/api/backup')
def backup(user=Depends(admin)):
    fd,path=tempfile.mkstemp(suffix='.sqlite3');os.close(fd)
    try:
        with database() as conn:
            dest=sqlite3.connect(path)
            try:conn.backup(dest)
            finally:dest.close()
    except Exception:
        os.unlink(path)
        raise
    return FileResponse(path,filename='mahax-fleet-backup.sqlite3',media_type='application/octet-stream',background=BackgroundTask(os.unlink,path))

@app.post('/api/demo/load')
def load_demo(user=Depends(admin)):
    from .demo import seed_demo
    with database(True) as conn:
        if conn.execute('SELECT 1 FROM records LIMIT 1').fetchone():fail('داده نمایشی فقط در پایگاه خالی بارگذاری می‌شود.',409)
        seed_demo(conn)
        cfg=settings(conn);cfg['data_mode']='demo';conn.execute('UPDATE settings SET data=? WHERE id=1',(json.dumps(cfg),));audit(conn,user,'demo_load')
    return {'ok':True}

@app.post('/api/demo/clear')
def clear_demo(user=Depends(admin)):
    with database(True) as conn:
        demo_ids={r[0] for r in conn.execute('SELECT id FROM records WHERE demo=1')}
        for kind,meta in CATALOG.items():
            refs=[f for f in meta['fields'] if f.get('source')]
            for row in records(conn,kind):
                if row['demo']:continue
                for f in refs:
                    value=row.get(f['key'])
                    if value in demo_ids if isinstance(value,str) else isinstance(value,list) and any(v in demo_ids for v in value):fail('رکورد واقعی به داده نمایشی مرتبط است؛ ابتدا ارتباط را اصلاح کنید.',409)
        conn.execute('DELETE FROM records WHERE demo=1')
        cfg=settings(conn);cfg['data_mode']='real';conn.execute('UPDATE settings SET data=? WHERE id=1',(json.dumps(cfg),));audit(conn,user,'demo_clear')
    return {'ok':True}

DIST=ROOT/'dist'
if DIST.exists() and not storage.is_hosted():
    app.mount('/',StaticFiles(directory=DIST,html=True),name='web')

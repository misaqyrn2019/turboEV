import csv
import io
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import app as server

PASSWORD='Test-Strong-Password-2026'

@pytest.fixture(params=['sqlite', 'libsql'])
def client(tmp_path,monkeypatch,request):
    monkeypatch.setattr(server,'DB_PATH',tmp_path/'test.sqlite3')
    monkeypatch.setenv('FLEET_ADMIN_PASSWORD',PASSWORD)
    if request.param == 'libsql':
        monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://test.invalid')
        monkeypatch.setattr(server.storage, 'connect', lambda path: server.storage.LibsqlConnection(str(path)))
    with TestClient(server.app) as c:
        result=c.post('/api/auth/login',json={'username':'admin','password':PASSWORD})
        assert result.status_code==200,result.text
        c.headers['X-CSRF-Token']=result.json()['csrf']
        yield c

def seed(c):
    response=c.post('/api/demo/load');assert response.status_code==200,response.text
    return c.get('/api/bootstrap').json()

def fields(data,kind,row):return {f['key']:row.get(f['key']) for f in data['catalog'][kind]['fields']}

def post(c,kind,body,expected=200):
    r=c.post('/api/records/'+kind,json=body)
    assert r.status_code==expected,r.text
    return r.json()

def test_session_csrf_logout_and_permissions(client):
    assert client.get('/api/bootstrap').status_code==200
    original=client.headers.pop('X-CSRF-Token')
    assert client.post('/api/records/centers',json={}).status_code==403
    client.headers['X-CSRF-Token']=original
    r=client.post('/api/users',json={'username':'viewer','name':'Viewer','role':'viewer','password':PASSWORD})
    assert r.status_code==200,r.text
    assert client.post('/api/auth/logout').status_code==200
    assert client.get('/api/bootstrap').status_code==401
    result=client.post('/api/auth/login',json={'username':'viewer','password':PASSWORD});assert result.status_code==200
    client.headers['X-CSRF-Token']=result.json()['csrf']
    assert client.get('/api/bootstrap').status_code==200
    assert client.post('/api/records/centers',json={'code':'C'}).status_code==403
    assert client.get('/api/backup').status_code==403
    assert client.get('/api/users').status_code==403

def test_password_hash_and_change(client):
    with server.database() as conn:
        hash=conn.execute('SELECT password_hash FROM users').fetchone()[0]
        assert hash.startswith('$argon2id$') and PASSWORD not in hash
    assert client.post('/api/auth/password',json={'current_password':'wrong','new_password':PASSWORD+'New'}).status_code==400
    assert client.post('/api/auth/password',json={'current_password':PASSWORD,'new_password':PASSWORD+'New'}).status_code==200
    assert client.post('/api/auth/logout').status_code==200
    assert client.post('/api/auth/login',json={'username':'admin','password':PASSWORD}).status_code==401
    assert client.post('/api/auth/login',json={'username':'admin','password':PASSWORD+'New'}).status_code==200

def test_crud_purchase_persistence_uniqueness_and_reference_protection(client):
    c=post(client,'centers',{'code':'C001','name':'مرکز جدید','city':'تهران'})
    f=post(client,'fleets',{'code':'F001','name':'ناوگان خرید','center_id':c['id']})
    v=post(client,'vehicles',{'code':'M001','model':'موتور جدید','type':'gasoline','fleet_id':f['id'],'purchase_price':150000000,'invoice':'INV-1','vin':'ABC123','purchase_date':'2026-09-20'})
    post(client,'vehicles',{'code':'M001','model':'دیگر','fleet_id':f['id']},409)
    post(client,'vehicles',{'code':'M002','model':'دیگر','type':'gasoline','fleet_id':f['id'],'vin':'ABC123'},409)
    assert client.delete('/api/records/fleets/'+f['id']).status_code==409
    with sqlite3.connect(server.DB_PATH) as other:
        row=other.execute('SELECT data FROM records WHERE id=?',(v['id'],)).fetchone()[0]
        assert '150000000' in row and 'INV-1' in row
    with TestClient(server.app) as restarted:
        login=restarted.post('/api/auth/login',json={'username':'admin','password':PASSWORD})
        assert login.status_code==200
        assert restarted.get('/api/bootstrap').json()['records']['vehicles'][0]['invoice']=='INV-1'
    assert client.delete('/api/records/vehicles/'+v['id']).status_code==200

def test_readiness_bms_and_conflicting_allocations(client):
    data=seed(client);r=data['records']
    ready=next(v for v in r['vehicles'] if v['code']=='M-001')
    body={'code':'MS-TEST','name':'مأموریت تست','vehicle_id':ready['id'],'driver_id':ready['driver_id'],'center_id':'demo-centers-1','status':'active','started_at':server.now()}
    one=post(client,'missions',body)
    body['code']='MS-CONFLICT';post(client,'missions',body,409)
    body.update(code='MS-BMS',vehicle_id='demo-vehicles-10',driver_id='demo-drivers-10');post(client,'missions',body,409)
    body.update(code='MS-LOW',vehicle_id='demo-vehicles-9',driver_id='demo-drivers-9',center_id='demo-centers-3');post(client,'missions',body,409)
    updated=client.get('/api/bootstrap').json();v=next(v for v in updated['records']['vehicles'] if v['id']==ready['id']);assert v['effective_status']=='mission'
    row=fields(data,'missions',one);row.update(status='completed',ended_at=server.now(),distance_km=12,soc_start=92,soc_end=75,result='انجام شد')
    assert client.put('/api/records/missions/'+one['id'],json=row).status_code==200
    fresh=client.get('/api/bootstrap').json()['records'];v=next(v for v in fresh['vehicles'] if v['id']==ready['id']);assert v['odometer']==ready['odometer']+12
    b=next(b for b in fresh['batteries'] if b['id']==ready['battery_id']);assert b['soc']==75
    assert client.put('/api/records/missions/'+one['id'],json=row).status_code==200
    assert next(v for v in client.get('/api/bootstrap').json()['records']['vehicles'] if v['id']==ready['id'])['odometer']==ready['odometer']+12
    row['status']='active';assert client.put('/api/records/missions/'+one['id'],json=row).status_code==409

def test_charging_updates_soc_and_enforces_exclusivity(client):
    data=seed(client)
    body={'code':'CH-TEST','vehicle_id':'demo-vehicles-1','charger_id':'demo-chargers-1','status':'charging','started_at':server.now(),'soc_start':40}
    charge=post(client,'charges',body)
    body.update(code='CH-CONFLICT',vehicle_id='demo-vehicles-4');post(client,'charges',body,409)
    row=fields(data,'charges',charge);row.update(status='completed',ended_at=server.now(),soc_end=95,energy_kwh=2.8)
    assert client.put('/api/records/charges/'+charge['id'],json=row).status_code==200
    bat=next(b for b in client.get('/api/bootstrap').json()['records']['batteries'] if b['id']=='demo-batteries-1');assert bat['soc']==95

def test_incident_out_of_service_timestamps_and_restore(client):
    data=seed(client);start=datetime.now(timezone.utc)-timedelta(hours=2)
    row=post(client,'incidents',{'code':'IN-TEST','title':'خرابی تست','vehicle_id':'demo-vehicles-1','owner':'تعمیرکار','reported_at':start.isoformat(),'severity':'critical'})
    assert next(v for v in client.get('/api/bootstrap').json()['records']['vehicles'] if v['id']=='demo-vehicles-1')['effective_status']=='out'
    body=fields(data,'incidents',row);body['status']='closed'
    assert client.put('/api/records/incidents/'+row['id'],json=body).status_code==422
    body.update(responded_at=(start+timedelta(minutes=20)).isoformat(),resolved_at=(start+timedelta(minutes=75)).isoformat(),restored_at=(start+timedelta(minutes=90)).isoformat(),resolution='تست و تأیید بازگشت')
    assert client.put('/api/records/incidents/'+row['id'],json=body).status_code==200
    v=next(v for v in client.get('/api/bootstrap').json()['records']['vehicles'] if v['id']=='demo-vehicles-1');assert v['effective_status']=='ready'
    assert server.parse_dt(body['restored_at'])-server.parse_dt(body['reported_at'])==timedelta(minutes=90)

def test_validation_and_atomic_csv(client):
    data=seed(client)
    battery=data['records']['batteries'][0];body=fields(data,'batteries',battery);body['soc']=101
    assert client.put('/api/records/batteries/'+battery['id'],json=body).status_code==422
    before=len(data['records']['centers'])
    response=client.post('/api/import/centers',json={'content':'code,name,city\nCSV1,مرکز اول,تهران\nCSV2,مرکز دوم,\n'})
    assert response.status_code==422
    assert len(client.get('/api/bootstrap').json()['records']['centers'])==before
    assert client.post('/api/import/centers',json={'content':'code,name,city\nCSV1,مرکز اول,تهران\nCSV2,مرکز دوم,کرج\n'}).json()['imported']==2
    post(client,'daily_logs',{'code':'LOG-BAD','vehicle_id':'demo-vehicles-1','date':'2026-01-01','planned_minutes':60,'available_minutes':80},422)

def test_backup_demo_safety_and_origin(client,tmp_path):
    data=seed(client)
    backup=client.get('/api/backup');assert backup.status_code==200
    path=tmp_path/'backup.sqlite3';path.write_bytes(backup.content)
    with sqlite3.connect(path) as conn:
        assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert conn.execute('SELECT count(*) FROM records').fetchone()[0]>100
    assert client.post('/api/demo/load').status_code==409
    real=post(client,'fleets',{'code':'REAL-F','name':'ناوگان واقعی','center_id':'demo-centers-1'})
    assert client.post('/api/demo/clear').status_code==409
    assert client.delete('/api/records/fleets/'+real['id']).status_code==200
    assert client.post('/api/demo/clear').status_code==200
    assert all(not r for r in client.get('/api/bootstrap').json()['records'].values())
    assert client.post('/api/records/centers',json={},headers={'Origin':'https://evil.example'}).status_code==403

def test_login_rate_limit(client):
    client.post('/api/auth/logout')
    for _ in range(5):assert client.post('/api/auth/login',json={'username':'admin','password':'wrong'}).status_code==401
    assert client.post('/api/auth/login',json={'username':'admin','password':PASSWORD}).status_code==429

def test_future_planning_and_historical_telemetry(client):
    data=seed(client)
    planned=post(client,'missions',{'code':'FUTURE','name':'آینده','vehicle_id':'demo-vehicles-1','driver_id':'demo-drivers-1','center_id':'demo-centers-1','status':'planned','started_at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()})
    body=fields(data,'missions',planned);body['status']='active'
    assert client.put('/api/records/missions/'+planned['id'],json=body).status_code==422
    yesterday=datetime.now(timezone.utc)-timedelta(days=1)
    post(client,'charges',{'code':'HISTORY','vehicle_id':'demo-vehicles-1','charger_id':'demo-chargers-1','status':'completed','started_at':(yesterday-timedelta(hours=2)).isoformat(),'ended_at':yesterday.isoformat(),'soc_start':20,'soc_end':100,'energy_kwh':2.5})
    battery=next(b for b in client.get('/api/bootstrap').json()['records']['batteries'] if b['id']=='demo-batteries-1')
    assert battery['soc']==92
    bad=fields(data,'batteries',battery);bad['measured_at']=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
    assert client.put('/api/records/batteries/'+battery['id'],json=bad).status_code==422

def test_fault_interrupts_charging_and_required_numeric_fields(client):
    data=seed(client)
    post(client,'incidents',{'code':'CH-FAULT','title':'خرابی در شارژ','vehicle_id':'demo-vehicles-9','owner':'اپراتور','reported_at':server.now(),'severity':'critical'})
    fresh=client.get('/api/bootstrap').json()['records'];charge=next(c for c in fresh['charges'] if c['id']=='demo-charges-1')
    assert charge['status']=='failed' and charge['ended_at']
    assert next(v for v in fresh['vehicles'] if v['id']=='demo-vehicles-9')['effective_status']=='out'
    row=fields(data,'vehicles',fresh['vehicles'][0]);row['odometer']=None
    assert client.put('/api/records/vehicles/'+fresh['vehicles'][0]['id'],json=row).status_code==422

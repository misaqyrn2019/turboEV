"""Deployment boundary checks; no production credentials or database needed."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend import app as server
from backend import storage

PASSWORD = 'Hosted-Test-Password-2026'


@pytest.fixture
def hosted(monkeypatch, tmp_path):
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('VERCEL_URL', 'test-deployment.vercel.app')
    monkeypatch.setenv('VERCEL_PROJECT_PRODUCTION_URL', 'test-production.vercel.app')
    monkeypatch.delenv('TURSO_DATABASE_URL', raising=False)
    monkeypatch.delenv('TURSO_AUTH_TOKEN', raising=False)
    monkeypatch.delenv('FLEET_ADMIN_PASSWORD', raising=False)
    monkeypatch.setattr(server, 'DB_PATH', tmp_path/'must-not-be-created'/'fleet.sqlite3')
    monkeypatch.setattr(server.app.state, 'database_ready', False)
    return tmp_path


def test_vercel_without_storage_fails_clearly_and_creates_no_local_db(hosted):
    # Deliberately no context manager: simulate a runtime without ASGI startup.
    client = TestClient(server.app, base_url='https://test-deployment.vercel.app')
    response = client.get('/api/health')
    assert response.status_code == 503
    assert response.headers['cache-control'] == 'no-store'
    assert 'Vercel' in response.json()['detail']
    assert client.post('/api/auth/login', json={'username':'admin','password':PASSWORD}).status_code == 503
    assert not server.DB_PATH.parent.exists()


def test_hosted_cold_start_login_csrf_and_persistence(hosted, monkeypatch):
    db_path = hosted/'remote-driver-test.sqlite3'
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://test.invalid')
    monkeypatch.setenv('FLEET_ADMIN_PASSWORD', PASSWORD)
    monkeypatch.setattr(storage, 'connect', lambda path: storage.LibsqlConnection(str(db_path)))
    url = 'https://test-deployment.vercel.app'
    client = TestClient(server.app, base_url=url)
    response = client.post('/api/auth/login', headers={'Origin':url}, json={'username':'admin','password':PASSWORD})
    assert response.status_code == 200, response.text
    assert 'Secure' in response.headers['set-cookie']
    assert 'HttpOnly' in response.headers['set-cookie']
    assert client.get('/api/auth/me').status_code == 200
    csrf = response.json()['csrf']
    assert client.post('/api/auth/logout', headers={'Origin':url}).status_code == 403
    assert client.post('/api/auth/logout', headers={'Origin':'https://unrelated.vercel.app', 'X-CSRF-Token':csrf}).status_code == 403
    assert client.get('/api/health', headers={'Host':'unrelated.vercel.app'}).status_code == 400
    assert client.get('/api/health', headers={'Host':'test-production.vercel.app'}).status_code == 200
    # A new worker must retain users/sessions and not reset the password.
    monkeypatch.setattr(server.app.state, 'database_ready', False)
    monkeypatch.delenv('FLEET_ADMIN_PASSWORD')
    assert client.get('/api/auth/me').status_code == 200
    assert client.get('/api/health').json()['storage'] == 'turso'
    assert client.post('/api/auth/logout', headers={'Origin':url, 'X-CSRF-Token':csrf}).status_code == 200
    assert client.get('/api/auth/me').status_code == 401
    assert not server.DB_PATH.parent.exists()


def test_remote_empty_db_requires_explicit_admin_password(hosted, monkeypatch):
    db_path = hosted/'empty-cloud.sqlite3'
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://test.invalid')
    monkeypatch.setattr(storage, 'connect', lambda path: storage.LibsqlConnection(str(db_path)))
    client = TestClient(server.app, base_url='https://test-deployment.vercel.app')
    assert client.get('/api/health').status_code == 503
    assert not server.app.state.database_ready
    monkeypatch.setenv('FLEET_ADMIN_PASSWORD', PASSWORD)
    assert client.get('/api/health').status_code == 200
    assert not list(hosted.rglob('initial-credentials.txt'))


def test_storage_configuration_never_falls_back_to_ephemeral_file(hosted, monkeypatch):
    with pytest.raises(storage.StorageConfigurationError):
        storage.connect(server.DB_PATH)
    monkeypatch.setenv('TURSO_DATABASE_URL', 'libsql://test.invalid')
    with pytest.raises(storage.StorageConfigurationError, match='TURSO_AUTH_TOKEN'):
        storage.connect(server.DB_PATH)
    monkeypatch.setenv('TURSO_AUTH_TOKEN', 'test-only-token')
    monkeypatch.setenv('TURSO_DATABASE_URL', 'http://test.invalid')
    with pytest.raises(storage.StorageConfigurationError, match='must use'):
        storage.connect(server.DB_PATH)


def test_libsql_transaction_rollback_and_snapshot_backup(tmp_path):
    connection = storage.LibsqlConnection(str(tmp_path/'source.sqlite3'))
    try:
        connection.execute('CREATE TABLE parent(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)')
        connection.execute('CREATE TABLE child(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))')
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('INSERT INTO parent(name) VALUES(?)', ('keep',))
        connection.execute('INSERT INTO child VALUES(1,1)')
        connection.commit()
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('INSERT INTO parent(name) VALUES(?)', ('rollback',))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute('INSERT INTO child VALUES(2,999)')
        connection.rollback()
        assert connection.execute('SELECT COUNT(*) FROM parent').fetchone()[0] == 1
        with sqlite3.connect(tmp_path/'backup.sqlite3') as destination:
            connection.backup(destination)
            assert destination.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert destination.execute('PRAGMA foreign_key_check').fetchall() == []
            assert destination.execute('SELECT name FROM parent').fetchone()[0] == 'keep'
    finally:
        connection.close()

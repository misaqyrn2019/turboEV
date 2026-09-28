"""SQLite locally; the same transactional SQL over libSQL for hosted deployments."""
from __future__ import annotations

import os
import sqlite3


class StorageConfigurationError(RuntimeError):
    pass


def remote_url():
    return os.environ.get('TURSO_DATABASE_URL', '').strip()


def is_hosted():
    return os.environ.get('VERCEL') == '1'


class Row(dict):
    """The application uses both named and positional sqlite3.Row access."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.columns = [column[0] for column in (cursor.description or ())]

    def fetchone(self):
        row = self.cursor.fetchone()
        return None if row is None else Row(zip(self.columns, row))

    def __iter__(self):
        while (row := self.fetchone()) is not None:
            yield row


class LibsqlConnection:
    """Use the official driver, retaining a single connection per transaction.

    Direct remote connections have no local replica or ephemeral writable DB.
    The driver currently raises ValueError for SQLite constraint errors.
    """
    def __init__(self, url, token=''):
        import libsql
        self.connection = libsql.connect(url, auth_token=token, isolation_level=None, timeout=15)

    def execute(self, sql, parameters=()):
        try:
            return Cursor(self.connection.execute(sql, tuple(parameters)))
        except ValueError as error:
            message = str(error)
            if 'constraint failed' in message.lower() or 'SQLITE_CONSTRAINT' in message:
                raise sqlite3.IntegrityError(message) from error
            raise sqlite3.OperationalError('Remote database query failed') from error

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()

    def backup(self, destination):
        # A read transaction gives all tables one consistent snapshot. The
        # returned backup remains an ordinary SQLite file usable offline.
        self.execute('BEGIN DEFERRED')
        try:
            schema = list(self.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type='table' DESC"))
            for entry in schema:
                if entry['type'] == 'table':
                    destination.execute(entry['sql'])
                    name = '"' + entry['name'].replace('"', '""') + '"'
                    rows = iter(self.execute(f'SELECT * FROM {name}'))
                    for row in rows:
                        placeholders = ','.join('?' for _ in row)
                        destination.execute(f'INSERT INTO {name} VALUES({placeholders})', tuple(row.values()))
            for entry in schema:
                if entry['type'] != 'table':
                    destination.execute(entry['sql'])
            if self.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").fetchone():
                destination.execute('DELETE FROM sqlite_sequence')
                for row in self.execute('SELECT name,seq FROM sqlite_sequence'):
                    destination.execute('INSERT INTO sqlite_sequence VALUES(?,?)', (row['name'], row['seq']))
            destination.commit()
        except Exception:
            destination.rollback()
            raise
        finally:
            self.rollback()


def connect(path):
    url = remote_url()
    if url:
        token = os.environ.get('TURSO_AUTH_TOKEN', '').strip()
        if not token:
            raise StorageConfigurationError('TURSO_AUTH_TOKEN is required')
        if not url.startswith(('libsql://', 'https://')):
            raise StorageConfigurationError('TURSO_DATABASE_URL must use libsql:// or https://')
        return LibsqlConnection(url, token)
    if is_hosted():
        raise StorageConfigurationError('TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are required on Vercel')
    connection = sqlite3.connect(path, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection

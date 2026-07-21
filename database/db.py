"""SQLite persistence layer with parameterized queries."""
from __future__ import annotations
import sqlite3, json
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator
from config.settings import settings
from utils.logger import log


class Database:
    def __init__(self, path) -> None:
        self.path = path
        self._init_schema()

    @contextmanager
    def conn(self) -> Iterator[sqlite3.Connection]:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    def _init_schema(self) -> None:
        with self.conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE, email TEXT,
                password_hash TEXT, salt TEXT,
                created_at TEXT, role TEXT DEFAULT 'analyst'
            );
            CREATE TABLE IF NOT EXISTS dashboards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, name TEXT, config TEXT,
                created_at TEXT, updated_at TEXT,
                UNIQUE(username, name)
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, action TEXT, resource TEXT,
                metadata TEXT, timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, filename TEXT, rows INTEGER,
                cols INTEGER, timestamp TEXT
            );
            """)

    def audit(self, username: str, action: str, resource: str = "", **meta) -> None:
        try:
            with self.conn() as c:
                c.execute(
                    "INSERT INTO audit_log(username, action, resource, metadata, timestamp) VALUES (?,?,?,?,?)",
                    (username, action, resource, json.dumps(meta), datetime.utcnow().isoformat())
                )
        except Exception as e:
            log.warning(f"Audit failed: {e}")

    def save_dashboard(self, username: str, name: str, config: dict) -> None:
        now = datetime.utcnow().isoformat()
        with self.conn() as c:
            c.execute("""
                INSERT INTO dashboards(username, name, config, created_at, updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(username, name) DO UPDATE SET config=excluded.config, updated_at=excluded.updated_at
            """, (username, name, json.dumps(config), now, now))

    def list_dashboards(self, username: str) -> list[dict]:
        with self.conn() as c:
            rows = c.execute("SELECT name, config, updated_at FROM dashboards WHERE username=?", (username,)).fetchall()
            return [{"name": r["name"], "config": json.loads(r["config"]), "updated_at": r["updated_at"]} for r in rows]

    def delete_dashboard(self, username: str, name: str) -> None:
        with self.conn() as c:
            c.execute("DELETE FROM dashboards WHERE username=? AND name=?", (username, name))

    def record_upload(self, username: str, filename: str, rows: int, cols: int) -> None:
        with self.conn() as c:
            c.execute("INSERT INTO uploads(username, filename, rows, cols, timestamp) VALUES(?,?,?,?,?)",
                      (username, filename, rows, cols, datetime.utcnow().isoformat()))


db = Database(settings.DB_PATH)
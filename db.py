import sqlite3
from typing import Optional
from models import User

DB_PATH = "shop.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id      INTEGER PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                phone      TEXT,
                email      TEXT,
                address    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

def get_user(tg_id: int) -> Optional[User]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT tg_id, username, first_name, last_name, phone, email, address, created_at "
            "FROM users WHERE tg_id = ?", (tg_id,)
        ).fetchone()
    return User(*row) if row else None

def add_user(tg_id: int, username: str, first_name: str, last_name: str) -> User:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (tg_id, username, first_name, last_name) "
            "VALUES (?, ?, ?, ?)",
            (tg_id, username, first_name, last_name)
        )
    return get_user(tg_id)
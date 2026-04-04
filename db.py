import sqlite3
from typing import Optional, List
from models import User, Category, Product

DB_PATH = "shop.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                tg_id      INTEGER PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                phone      TEXT,
                email      TEXT,
                address    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS categories (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER REFERENCES categories(id),
                name        TEXT NOT NULL,
                description TEXT,
                price       REAL NOT NULL,
                stock       INTEGER DEFAULT 0,
                photo_id    TEXT
            );
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

def update_user_field(tg_id: int, field: str, value: str):
    allowed = {"phone", "email", "address"}
    if field not in allowed:
        raise ValueError(f"Field {field} is not allowed")
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {field} = ? WHERE tg_id = ?", (value, tg_id))

# --- categories ---
def get_categories(type1: str = None) -> List[Category]:
    with get_conn() as conn:
        if type1:
            rows = conn.execute("SELECT id, name, type FROM categories WHERE type = ?", (type1,)).fetchall()
        else:
            rows = conn.execute("SELECT id, name, type FROM categories").fetchall()
    return [Category(*r) for r in rows]

def add_category(name: str, type1: str) -> Category:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO categories (name, type) VALUES (?, ?)", (name, type1))
        return Category(cur.lastrowid, name, type1)

# --- products ---
def get_products(category_id: int) -> List[Product]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category_id, name, price, description, stock, photo_id "
            "FROM products WHERE category_id = ?", (category_id,)
        ).fetchall()
    return [Product(*r) for r in rows]

def add_product(category_id: int, name: str, description: str,
                price: float, stock: int, photo_id: str = None) -> Product:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (category_id, name, description, price, stock, photo_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (category_id, name, description, price, stock, photo_id)
        )
        return Product(cur.lastrowid, category_id, name, price, description, stock, photo_id)

def get_all_products() -> List[Product]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category_id, name, price, description, stock, photo_id FROM products"
        ).fetchall()
    return [Product(*r) for r in rows]
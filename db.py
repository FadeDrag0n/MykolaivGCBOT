import sqlite3
from typing import Optional, List
from models import User, Category, Product, CartItem, Order, OrderItem, OrderStatus

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
            CREATE TABLE IF NOT EXISTS cart (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id      INTEGER NOT NULL REFERENCES users(tg_id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity   INTEGER NOT NULL DEFAULT 1,
                UNIQUE(tg_id, product_id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id      INTEGER NOT NULL REFERENCES users(tg_id),
                status     TEXT NOT NULL DEFAULT 'new',
                phone      TEXT NOT NULL,
                address    TEXT,
                comment    TEXT,
                total      REAL NOT NULL,
                ttn        TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id     INTEGER NOT NULL REFERENCES orders(id),
                product_id   INTEGER REFERENCES products(id),
                product_name TEXT NOT NULL,
                price        REAL NOT NULL,
                quantity     INTEGER NOT NULL
            );
        """)
        # Migration: add ttn column if missing (for existing DBs)
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN ttn TEXT")
        except Exception:
            pass

# ── users ──────────────────────────────────────────────────────────────────────

def get_user(tg_id: int) -> Optional[User]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT tg_id, username, first_name, last_name, phone, email, address, created_at "
            "FROM users WHERE tg_id = ?", (tg_id,)
        ).fetchone()
    return User(*row) if row else None

def get_all_users() -> List[User]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT tg_id, username, first_name, last_name, phone, email, address, created_at "
            "FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [User(*r) for r in rows]

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

def count_user_orders(tg_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE tg_id = ? AND status = 'done'", (tg_id,)
        ).fetchone()
    return row[0] if row else 0

# ── categories ─────────────────────────────────────────────────────────────────

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

def update_category(cat_id: int, name: str = None, type1: str = None):
    with get_conn() as conn:
        if name:
            conn.execute("UPDATE categories SET name = ? WHERE id = ?", (name, cat_id))
        if type1:
            conn.execute("UPDATE categories SET type = ? WHERE id = ?", (type1, cat_id))

def delete_category(cat_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))

def get_category(cat_id: int) -> Optional[Category]:
    with get_conn() as conn:
        row = conn.execute("SELECT id, name, type FROM categories WHERE id = ?", (cat_id,)).fetchone()
    return Category(*row) if row else None

# ── products ───────────────────────────────────────────────────────────────────

def get_products(category_id: int, sort: str = "default") -> List[Product]:
    """
    sort: 'default' | 'price_asc' | 'price_desc' | 'in_stock'
    """
    order_clause = {
        "price_asc":  "ORDER BY price ASC",
        "price_desc": "ORDER BY price DESC",
        "in_stock":   "ORDER BY stock DESC",
    }.get(sort, "")
    where = "WHERE category_id = ?"
    if sort == "in_stock":
        where = "WHERE category_id = ? AND stock > 0"
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT id, category_id, name, price, description, stock, photo_id "
            f"FROM products {where} {order_clause}",
            (category_id,)
        ).fetchall()
    return [Product(*r) for r in rows]

def search_products(query: str) -> List[Product]:
    """Full-text search by name and description."""
    q = f"%{query.strip()}%"
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category_id, name, price, description, stock, photo_id "
            "FROM products WHERE name LIKE ? OR description LIKE ? "
            "ORDER BY CASE WHEN stock > 0 THEN 0 ELSE 1 END, name",
            (q, q)
        ).fetchall()
    return [Product(*r) for r in rows]

def get_product_by_id(product_id: int) -> Optional[Product]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, category_id, name, price, description, stock, photo_id "
            "FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    return Product(*row) if row else None

def add_product(category_id: int, name: str, description: str,
                price: float, stock: int, photo_id: str = None) -> Product:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (category_id, name, description, price, stock, photo_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (category_id, name, description, price, stock, photo_id)
        )
        return Product(cur.lastrowid, category_id, name, price, description, stock, photo_id)

def update_product(product_id: int, **kwargs):
    allowed = {"name", "description", "price", "stock", "photo_id", "category_id"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE products SET {set_clause} WHERE id = ?", values)

def delete_product(product_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))

def get_all_products() -> List[Product]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category_id, name, price, description, stock, photo_id FROM products"
        ).fetchall()
    return [Product(*r) for r in rows]

# ── cart ───────────────────────────────────────────────────────────────────────

def cart_set_quantity(tg_id: int, product_id: int, quantity: int):
    if quantity <= 0:
        cart_remove(tg_id, product_id)
        return
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cart (tg_id, product_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(tg_id, product_id) DO UPDATE SET quantity = excluded.quantity",
            (tg_id, product_id, quantity)
        )

def cart_remove(tg_id: int, product_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE tg_id = ? AND product_id = ?", (tg_id, product_id))

def cart_clear(tg_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM cart WHERE tg_id = ?", (tg_id,))

def cart_get(tg_id: int) -> List[CartItem]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT c.id, c.tg_id, c.product_id, c.quantity,
                      p.name, p.price, p.photo_id, p.stock
               FROM cart c
               JOIN products p ON p.id = c.product_id
               WHERE c.tg_id = ?
               ORDER BY c.id""",
            (tg_id,)
        ).fetchall()
    return [CartItem(*r) for r in rows]

def cart_item_get(tg_id: int, product_id: int) -> Optional[CartItem]:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT c.id, c.tg_id, c.product_id, c.quantity,
                      p.name, p.price, p.photo_id, p.stock
               FROM cart c
               JOIN products p ON p.id = c.product_id
               WHERE c.tg_id = ? AND c.product_id = ?""",
            (tg_id, product_id)
        ).fetchone()
    return CartItem(*row) if row else None

# ── orders ─────────────────────────────────────────────────────────────────────

def _row_to_order(row) -> Order:
    return Order(
        id=row[0], tg_id=row[1], status=row[2], phone=row[3],
        address=row[4], comment=row[5], total=row[6], created_at=row[7],
        ttn=row[8] if len(row) > 8 else None,
        username=row[9] if len(row) > 9 else None,
        first_name=row[10] if len(row) > 10 else None,
        last_name=row[11] if len(row) > 11 else None,
    )

def create_order(tg_id: int, phone: str, address: str, comment: str,
                 items: List[CartItem]) -> Order:
    total = sum(i.product_price * i.quantity for i in items)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO orders (tg_id, status, phone, address, comment, total) VALUES (?,?,?,?,?,?)",
            (tg_id, OrderStatus.NEW.value, phone, address, comment, total)
        )
        order_id = cur.lastrowid
        for item in items:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, price, quantity) "
                "VALUES (?,?,?,?,?)",
                (order_id, item.product_id, item.product_name, item.product_price, item.quantity)
            )
            # Зменшуємо stock
            conn.execute(
                "UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?",
                (item.quantity, item.product_id)
            )
    return get_order(order_id)

def get_order(order_id: int) -> Optional[Order]:
    with get_conn() as conn:
        row = conn.execute(
            """SELECT o.id, o.tg_id, o.status, o.phone, o.address, o.comment, o.total, o.created_at,
                      o.ttn, u.username, u.first_name, u.last_name
               FROM orders o LEFT JOIN users u ON u.tg_id = o.tg_id
               WHERE o.id = ?""", (order_id,)
        ).fetchone()
        if not row:
            return None
        order = _row_to_order(row)
        order.items = _get_order_items(conn, order_id)
    return order

def _get_order_items(conn, order_id: int) -> List[OrderItem]:
    rows = conn.execute(
        "SELECT id, order_id, product_id, product_name, price, quantity "
        "FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    return [OrderItem(*r) for r in rows]

def get_orders_by_user(tg_id: int) -> List[Order]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, tg_id, status, phone, address, comment, total, created_at, ttn "
            "FROM orders WHERE tg_id = ? ORDER BY created_at DESC", (tg_id,)
        ).fetchall()
        orders = [_row_to_order(r) for r in rows]
        for o in orders:
            o.items = _get_order_items(conn, o.id)
    return orders

def get_all_orders(active_only: bool = False) -> List[Order]:
    from models import ACTIVE_STATUSES
    with get_conn() as conn:
        if active_only:
            placeholders = ",".join("?" * len(ACTIVE_STATUSES))
            statuses = [s.value for s in ACTIVE_STATUSES]
            rows = conn.execute(
                f"""SELECT o.id, o.tg_id, o.status, o.phone, o.address, o.comment,
                           o.total, o.created_at, o.ttn, u.username, u.first_name, u.last_name
                    FROM orders o LEFT JOIN users u ON u.tg_id = o.tg_id
                    WHERE o.status IN ({placeholders})
                    ORDER BY o.created_at DESC""", statuses
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT o.id, o.tg_id, o.status, o.phone, o.address, o.comment,
                          o.total, o.created_at, o.ttn, u.username, u.first_name, u.last_name
                   FROM orders o LEFT JOIN users u ON u.tg_id = o.tg_id
                   ORDER BY o.created_at DESC"""
            ).fetchall()
        orders = [_row_to_order(r) for r in rows]
        for o in orders:
            o.items = _get_order_items(conn, o.id)
    return orders

def update_order_status(order_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

def update_order_ttn(order_id: int, ttn: str):
    with get_conn() as conn:
        conn.execute("UPDATE orders SET ttn = ? WHERE id = ?", (ttn, order_id))

def restore_stock_for_order(order_id: int):
    """Повертає stock при скасуванні замовлення."""
    with get_conn() as conn:
        items = conn.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)
        ).fetchall()
        for product_id, qty in items:
            conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?", (qty, product_id)
            )

# ── stats ──────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders WHERE status='done'"
        ).fetchone()
        revenue_all = row[0]

        row = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders "
            "WHERE status='done' AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        ).fetchone()
        revenue_month = row[0]

        row = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
        orders_all = row[0]

        row = conn.execute(
            "SELECT COUNT(*) FROM orders "
            "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        ).fetchone()
        orders_month = row[0]

        row = conn.execute(
            """SELECT oi.product_name, SUM(oi.price * oi.quantity) as rev
               FROM order_items oi JOIN orders o ON o.id = oi.order_id
               WHERE o.status = 'done'
               GROUP BY oi.product_name ORDER BY rev DESC LIMIT 1"""
        ).fetchone()
        top_revenue_product = row

        row = conn.execute(
            """SELECT oi.product_name, SUM(oi.quantity) as qty
               FROM order_items oi JOIN orders o ON o.id = oi.order_id
               WHERE o.status = 'done'
               GROUP BY oi.product_name ORDER BY qty DESC LIMIT 1"""
        ).fetchone()
        top_qty_product = row

    return {
        "revenue_all": revenue_all,
        "revenue_month": revenue_month,
        "orders_all": orders_all,
        "orders_month": orders_month,
        "top_revenue_product": top_revenue_product,
        "top_qty_product": top_qty_product,
    }
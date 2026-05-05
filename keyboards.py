from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from models import OrderStatus, ORDER_STATUS_LABELS

CATALOG_PAGE_SIZE = 5

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🌿 Каталог товарів"), KeyboardButton("❓ Допомога"))
    kb.row(KeyboardButton("🛒 Корзина"), KeyboardButton("📦 Мої замовлення"))
    kb.row(KeyboardButton("👤 Контактна інформація"), KeyboardButton("🔍 Пошук товарів"))
    return kb

def category():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🐾 Тварини", callback_data="cat_animals"),
        InlineKeyboardButton("🌿 Рослини", callback_data="cat_plants"),
    )
    return kb

def subcategories(categories: list, back_type: str):
    kb = InlineKeyboardMarkup()
    for cat in categories:
        icon = "🐾" if cat.type == "animals" else "🌿"
        kb.add(InlineKeyboardButton(f"{icon} {cat.name}", callback_data=f"subcat_{cat.id}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="catalog_back"))
    return kb

def catalog_filters(cat_id: int, current_sort: str = "default"):
    """Фільтри сортування для каталогу."""
    sorts = [
        ("default",    "📋 За замовч."),
        ("price_asc",  "💰 Ціна ↑"),
        ("price_desc", "💰 Ціна ↓"),
        ("in_stock",   "✅ В наявності"),
    ]
    kb = InlineKeyboardMarkup()
    row = []
    for key, label in sorts:
        mark = "▪️" if key == current_sort else ""
        row.append(InlineKeyboardButton(f"{mark}{label}", callback_data=f"catsort_{cat_id}_{key}"))
        if len(row) == 2:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    return kb

def catalog_pagination(cat_id: int, page: int, total: int, sort: str = "default"):
    """Кнопки навігації між сторінками каталогу."""
    kb = InlineKeyboardMarkup()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Назад", callback_data=f"catpage_{cat_id}_{page-1}_{sort}"))
    last_page = (total - 1) // CATALOG_PAGE_SIZE
    if page < last_page:
        nav.append(InlineKeyboardButton("▶️ Далі", callback_data=f"catpage_{cat_id}_{page+1}_{sort}"))
    if nav:
        kb.row(*nav)
    kb.add(InlineKeyboardButton(f"📄 {page+1}/{last_page+1}", callback_data="noop"))
    kb.add(InlineKeyboardButton("🔙 До підкатегорій", callback_data=f"back_subcat_cat_{cat_id}"))
    return kb

def product_card(product_id: int, in_cart: bool = False):
    kb = InlineKeyboardMarkup()
    if in_cart:
        kb.add(InlineKeyboardButton("✅ У кошику — змінити кількість", callback_data=f"cart_qty_{product_id}"))
    else:
        kb.add(InlineKeyboardButton("🛒 Додати у кошик", callback_data=f"cart_add_{product_id}"))
    kb.add(InlineKeyboardButton("🔙 Назад до категорії", callback_data=f"back_to_subcat_{product_id}"))
    return kb

def cart_item_actions(product_id: int, quantity: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("➖", callback_data=f"cqty_minus_{product_id}"),
        InlineKeyboardButton(f"  {quantity}  ", callback_data="noop"),
        InlineKeyboardButton("➕", callback_data=f"cqty_plus_{product_id}"),
    )
    kb.row(
        InlineKeyboardButton("🗑 Видалити", callback_data=f"cqty_remove_{product_id}"),
        InlineKeyboardButton("✅ Готово", callback_data=f"cqty_done_{product_id}"),
    )
    return kb

def cart_view(items: list):
    kb = InlineKeyboardMarkup()
    for item in items:
        kb.add(InlineKeyboardButton(
            f"❌ {item.product_name} × {item.quantity}",
            callback_data=f"cart_del_{item.product_id}"
        ))
    if items:
        kb.row(
            InlineKeyboardButton("🗑 Очистити кошик", callback_data="cart_clear"),
            InlineKeyboardButton("✅ Оформити", callback_data="cart_checkout"),
        )
    kb.add(InlineKeyboardButton("🛍 До каталогу", callback_data="catalog_back_main"))
    return kb

def request_phone():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Поділитися номером", request_contact=True))
    kb.add(KeyboardButton("🔙 Скасувати"))
    return kb

def info():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Номер телефону", callback_data="info_phone"),
        InlineKeyboardButton("Пошта", callback_data="info_email"),
    )
    kb.row(InlineKeyboardButton("Адреса", callback_data="info_address"))
    return kb

def cancel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🔙 Скасувати"))
    return kb

def add_product_categories(categories: list):
    kb = InlineKeyboardMarkup()
    for cat in categories:
        icon = "🐾" if cat.type == "animals" else "🌿"
        kb.add(InlineKeyboardButton(f"{icon} {cat.name}", callback_data=f"apc_{cat.id}"))
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="addproduct_cancel"))
    return kb

def edit_product_list(products: list):
    kb = InlineKeyboardMarkup()
    for p in products:
        kb.add(InlineKeyboardButton(f"✏️ {p.name} — {p.price} грн", callback_data=f"edit_p_{p.id}"))
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="editproduct_cancel"))
    return kb

def edit_product_fields(product_id: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📝 Назва", callback_data=f"epf_name_{product_id}"),
        InlineKeyboardButton("📄 Опис", callback_data=f"epf_desc_{product_id}"),
    )
    kb.row(
        InlineKeyboardButton("💰 Ціна", callback_data=f"epf_price_{product_id}"),
        InlineKeyboardButton("📦 Залишок", callback_data=f"epf_stock_{product_id}"),
    )
    kb.row(InlineKeyboardButton("🖼 Фото", callback_data=f"epf_photo_{product_id}"))
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="editproduct_cancel"))
    return kb

def remove_product_list(products: list):
    kb = InlineKeyboardMarkup()
    for p in products:
        kb.add(InlineKeyboardButton(f"🗑 {p.name} — {p.price} грн", callback_data=f"rm_p_{p.id}"))
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="removeproduct_cancel"))
    return kb

def confirm_remove(product_id: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Так, видалити", callback_data=f"rm_confirm_{product_id}"),
        InlineKeyboardButton("❌ Ні", callback_data="removeproduct_cancel"),
    )
    return kb

# ── Orders (user) ──────────────────────────────────────────────────────────────

def order_card_user(order_id: int, can_cancel: bool = False):
    kb = InlineKeyboardMarkup()
    if can_cancel:
        kb.add(InlineKeyboardButton("❌ Скасувати замовлення", callback_data=f"user_cancel_order_{order_id}"))
    return kb

def confirm_cancel_order(order_id: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Так, скасувати", callback_data=f"user_cancel_confirm_{order_id}"),
        InlineKeyboardButton("🔙 Ні", callback_data=f"user_cancel_no_{order_id}"),
    )
    return kb

# ── Admin panel ────────────────────────────────────────────────────────────────

def admin_panel():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📦 Товари", callback_data="adm_products"),
        InlineKeyboardButton("🗂 Категорії", callback_data="adm_categories"),
    )
    kb.row(
        InlineKeyboardButton("👥 Користувачі", callback_data="adm_users"),
        InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
    )
    kb.row(
        InlineKeyboardButton("🔔 Активні замовлення", callback_data="adm_orders_active"),
        InlineKeyboardButton("📋 Всі замовлення", callback_data="adm_orders_all"),
    )
    kb.add(InlineKeyboardButton("📢 Розсилка", callback_data="adm_broadcast"))
    return kb

def admin_categories(categories: list):
    kb = InlineKeyboardMarkup()
    for cat in categories:
        icon = "🐾" if cat.type == "animals" else "🌿"
        kb.add(InlineKeyboardButton(f"{icon} {cat.name}", callback_data=f"adm_cat_{cat.id}"))
    kb.row(
        InlineKeyboardButton("➕ Додати категорію", callback_data="adm_cat_add"),
        InlineKeyboardButton("🔙 Назад", callback_data="adm_back"),
    )
    return kb

def admin_category_actions(cat_id: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✏️ Перейменувати", callback_data=f"adm_cat_rename_{cat_id}"),
        InlineKeyboardButton("🗑 Видалити", callback_data=f"adm_cat_del_{cat_id}"),
    )
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="adm_categories"))
    return kb

def admin_cat_type():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🐾 Тварини", callback_data="adm_cat_type_animals"),
        InlineKeyboardButton("🌿 Рослини", callback_data="adm_cat_type_plants"),
    )
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="adm_categories"))
    return kb

def admin_confirm_cat_del(cat_id: int):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Так", callback_data=f"adm_cat_del_confirm_{cat_id}"),
        InlineKeyboardButton("❌ Ні", callback_data="adm_categories"),
    )
    return kb

def admin_users_list(users: list, page: int = 0, per_page: int = 8):
    kb = InlineKeyboardMarkup()
    start = page * per_page
    chunk = users[start:start + per_page]
    for u in chunk:
        name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username or str(u.tg_id)
        kb.add(InlineKeyboardButton(f"👤 {name}", callback_data=f"adm_user_{u.tg_id}"))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"adm_users_page_{page-1}"))
    if start + per_page < len(users):
        nav.append(InlineKeyboardButton("▶️", callback_data=f"adm_users_page_{page+1}"))
    if nav:
        kb.row(*nav)
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="adm_back"))
    return kb

def admin_order_statuses(order_id: int, current_status: str):
    kb = InlineKeyboardMarkup()
    for status in OrderStatus:
        label = ORDER_STATUS_LABELS[status]
        mark = "✔️ " if status.value == current_status else ""
        kb.add(InlineKeyboardButton(
            f"{mark}{label}", callback_data=f"adm_ord_status_{order_id}_{status.value}"
        ))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="adm_orders_active"))
    return kb

def admin_order_card(order_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔄 Змінити статус", callback_data=f"adm_ord_change_{order_id}"))
    kb.add(InlineKeyboardButton("🔙 До замовлень", callback_data="adm_orders_active"))
    return kb

def admin_broadcast_confirm():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Надіслати всім", callback_data="adm_broadcast_confirm"),
        InlineKeyboardButton("❌ Скасувати", callback_data="adm_broadcast_cancel"),
    )
    return kb
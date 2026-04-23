from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🌿 Каталог товарів"), KeyboardButton("❓ Допомога"))
    kb.row(KeyboardButton("🛒 Корзина"), KeyboardButton("📦 Мої замовлення"))
    kb.row(KeyboardButton("👤 Контактна інформація"))
    return kb

def category():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🐾 Тварини", callback_data="cat_animals"),
        InlineKeyboardButton("🌿 Рослини", callback_data="cat_plants"),
    )
    return kb

def subcategories(categories: list, back_type: str):
    """List of subcategories for a given type (animals/plants)."""
    kb = InlineKeyboardMarkup()
    for cat in categories:
        icon = "🐾" if cat.type == "animals" else "🌿"
        kb.add(InlineKeyboardButton(f"{icon} {cat.name}", callback_data=f"subcat_{cat.id}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="catalog_back"))
    return kb

def product_card(product_id: int, in_cart: bool = False):
    """Inline keyboard under a product card."""
    kb = InlineKeyboardMarkup()
    if in_cart:
        kb.add(InlineKeyboardButton("✅ У кошику — змінити кількість", callback_data=f"cart_qty_{product_id}"))
    else:
        kb.add(InlineKeyboardButton("🛒 Додати у кошик", callback_data=f"cart_add_{product_id}"))
    kb.add(InlineKeyboardButton("🔙 Назад до категорії", callback_data=f"back_to_subcat_{product_id}"))
    return kb

def cart_item_actions(product_id: int, quantity: int):
    """Keyboard shown when user taps 'Додати у кошик' or 'змінити кількість'."""
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
    """Keyboard for the cart view."""
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

def info():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Номер телефону", callback_data="info_phone"),
        InlineKeyboardButton("Пошта", callback_data="info_email"),
    )
    kb.row(
        InlineKeyboardButton("Адреса", callback_data="info_address")
    )
    return kb

def cancel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🔙 Скасувати"))
    return kb

def add_product_categories(categories: list):
    kb = InlineKeyboardMarkup()
    for cat in categories:
        icon = "🐾" if cat.type == "animals" else "🌿"
        kb.add(InlineKeyboardButton(
            f"{icon} {cat.name}", callback_data=f"apc_{cat.id}"
        ))
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="addproduct_cancel"))
    return kb

def edit_product_list(products: list):
    """List of products for edit selection."""
    kb = InlineKeyboardMarkup()
    for p in products:
        kb.add(InlineKeyboardButton(f"✏️ {p.name} — {p.price} грн", callback_data=f"edit_p_{p.id}"))
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="editproduct_cancel"))
    return kb

def edit_product_fields(product_id: int):
    """Which field to edit."""
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📝 Назва", callback_data=f"epf_name_{product_id}"),
        InlineKeyboardButton("📄 Опис", callback_data=f"epf_desc_{product_id}"),
    )
    kb.row(
        InlineKeyboardButton("💰 Ціна", callback_data=f"epf_price_{product_id}"),
        InlineKeyboardButton("📦 Залишок", callback_data=f"epf_stock_{product_id}"),
    )
    kb.row(
        InlineKeyboardButton("🖼 Фото", callback_data=f"epf_photo_{product_id}"),
    )
    kb.add(InlineKeyboardButton("❌ Скасувати", callback_data="editproduct_cancel"))
    return kb

def remove_product_list(products: list):
    """List of products for removal."""
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
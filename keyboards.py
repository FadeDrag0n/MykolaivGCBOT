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
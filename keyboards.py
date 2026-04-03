from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🌿 Каталог товарів", "❓ Допомога")
    kb.row("🛒 Корзина", "📦 Мої замовлення")
    return kb

def category():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🐾 Тварини", "🌿 Рослини")
    kb.row("⬅️ Головне меню")
    return kb
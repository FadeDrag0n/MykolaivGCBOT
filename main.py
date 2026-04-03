import os
import telebot
from dotenv import load_dotenv
import ua
from telebot.types import BotCommand, BotCommandScopeChat
from handlers import catalog
import keyboards as kb

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

def setup_commands(bot1, admin_id):
    user_commands = [
        BotCommand("start",   "Головне меню"),
        BotCommand("catalog", "Каталог товарів"),
        BotCommand("cart",    "Моя корзина"),
        BotCommand("orders",  "Історія товарів"),
        BotCommand("help",    "Допомога"),
        BotCommand("cancel",  "Відмінити дію"),
    ]

    admin_commands = user_commands + [
        BotCommand("admin",         "Панель адміністратора"),
        BotCommand("addproduct",    "Додати товар"),
        BotCommand("editproduct", "Відредагувати товар"),
        BotCommand("removeproduct", "прибрати товар"),
        BotCommand("orders_all",    "Усі замовлення"),
        BotCommand("stats",         "Статистика"),
    ]

    bot1.set_my_commands(user_commands)
    bot1.set_my_commands(admin_commands, scope=BotCommandScopeChat(admin_id))

catalog.register(bot)

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, ua.START_MESSAGE, reply_markup=kb.main_menu())

@bot.message_handler(func=lambda m: m.text == "⬅️ Головне меню")
def back_to_main(message):
    bot.send_message(message.chat.id, ua.START_MESSAGE, reply_markup=kb.main_menu())

@bot.message_handler(commands=["help"])
@bot.message_handler(func=lambda m: m.text == "❓ Допомога")
def help_handler(message):
    is_admin = message.from_user.id == ADMIN_ID

    user_text = ua.USER_HELP

    admin_text = user_text + ua.ADMIN_HELP

    text = admin_text if is_admin else user_text

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=kb.main_menu(),
    )

@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    bot.reply_to(message, ua.UNKNOWN_MESSAGE)

bot.infinity_polling()
# bot.polling(non_stop=True)
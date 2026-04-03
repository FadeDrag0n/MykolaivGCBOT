import os
import telebot
from dotenv import load_dotenv
import ua
from telebot.types import BotCommand, BotCommandScopeChat
from handlers import catalog
import keyboards as kb
import db

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)
db.init_db()

def setup_commands(bot1, admin_id):
    user_commands = [
        BotCommand("start",   "Головне меню"),
        BotCommand("catalog", "Каталог товарів"),
        BotCommand("cart",    "Моя корзина"),
        BotCommand("orders",  "Історія товарів"),
        BotCommand("help",    "Допомога"),
        BotCommand("info", "Контактна інформація"),
    ]

    admin_commands = user_commands + [
        BotCommand("admin",         "Панель адміністратора"),
        BotCommand("addproduct",    "Додати товар"),
        BotCommand("editproduct", "Відредагувати товар"),
        BotCommand("removeproduct", "прибрати товар"),
        BotCommand("orders_all",    "Усі замовлення"),
        BotCommand("stats",         "Статистика"),
    ]

    # bot1.delete_my_commands()
    bot1.set_my_commands(user_commands)
    bot1.set_my_commands(admin_commands, scope=BotCommandScopeChat(admin_id))

catalog.register(bot)

@bot.message_handler(commands=['start'])
def main(message):
    db.add_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    bot.send_message(message.chat.id, ua.START_MESSAGE, reply_markup=kb.main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "main_menu")
def back_to_main(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, ua.START_MESSAGE, reply_markup=kb.main_menu())

@bot.message_handler(commands=["help"])
@bot.message_handler(func=lambda m: m.text == "❓ Допомога")
def help_handler(message):
    is_admin = message.from_user.id == ADMIN_ID
    text = ua.USER_HELP + ua.ADMIN_HELP if is_admin else ua.USER_HELP
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb.main_menu())

@bot.message_handler(func=lambda m: m.text == "👤 Контактна інформація")
def info_handler(message):
    user = db.get_user(tg_id=message.from_user.id)
    bot.send_message(message.chat.id, ua.info_message(message.from_user.username, user.phone, user.email, user.address), reply_markup=kb.info())


@bot.message_handler(func=lambda message: True)
def unknown_message(message):
    bot.reply_to(message, ua.UNKNOWN_MESSAGE)


#setup_commands(bot, ADMIN_ID)
bot.infinity_polling()
# bot.polling(non_stop=True)
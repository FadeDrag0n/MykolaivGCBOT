import os
import telebot
from dotenv import load_dotenv
from telebot import custom_filters
import ua
from telebot.types import BotCommand, BotCommandScopeChat
import keyboards as kb
import db
from telebot.storage import StateMemoryStorage
from handlers import catalog, info, admin
load_dotenv()


TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=storage)
bot.add_custom_filter(custom_filters.StateFilter(bot))
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

@bot.message_handler(commands=["cancel"], state="*")
@bot.message_handler(func=lambda m: m.text == "🔙 Скасувати", state="*")
def cancel(message):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "Скасовано ✅", reply_markup=kb.main_menu())

catalog.register(bot)
info.register(bot)
admin.register(bot, ADMIN_ID)

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


@bot.message_handler(state= None, func=lambda message: True)
def unknown_message(message):
    bot.reply_to(message, ua.UNKNOWN_MESSAGE)


#setup_commands(bot, ADMIN_ID)
bot.infinity_polling(skip_pending=True)
# bot.polling(non_stop=True)
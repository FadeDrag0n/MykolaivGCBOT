import os
import telebot
from dotenv import load_dotenv
import ua

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, ua.START_MESSAGE)


bot.polling(none_stop=True)
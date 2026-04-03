import ua
import keyboards as kb

def register(bot):

    @bot.message_handler(commands=["catalog"])
    @bot.message_handler(func=lambda m: m.text == "🌿 Каталог товарів")
    def catalog(message):
        bot.send_message(message.chat.id, ua.CATALOG_OPEN, reply_markup=kb.category())
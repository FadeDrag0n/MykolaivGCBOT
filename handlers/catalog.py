import ua
import keyboards as kb

def register(bot):

    @bot.message_handler(commands=["catalog"])
    @bot.message_handler(func=lambda m: m.text == "🌿 Каталог товарів")
    def catalog(message):
        bot.send_message(message.chat.id, ua.CATALOG_OPEN, reply_markup=kb.category())

    @bot.callback_query_handler(func=lambda c: c.data == "cat_animals")
    def animals(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Товари для тварин 🐾")

    @bot.callback_query_handler(func=lambda c: c.data == "cat_plants")
    def plants(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Товари для рослин 🌿")
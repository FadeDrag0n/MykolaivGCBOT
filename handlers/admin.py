import db
import keyboards as kb
from telebot.handler_backends import State, StatesGroup

class AddProductStates(StatesGroup):
    category    = State()
    name        = State()
    description = State()
    price       = State()
    stock       = State()
    photo       = State()

def register(bot, admin_id):

    def is_admin(message):
        return message.from_user.id == admin_id

    @bot.message_handler(func=lambda m: m.text == "🔙 Скасувати")
    def cancel_by_button(message):
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "❌ Додавання скасовано", reply_markup=kb.main_menu())

    @bot.message_handler(commands=["addproduct"])
    def addproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу")
            return

        categories = db.get_categories()
        if not categories:
            db.add_category("Корм", "animals")
            db.add_category("Аксесуари", "animals")
            db.add_category("Добрива", "plants")
            db.add_category("Ґрунти", "plants")
            categories = db.get_categories()

        bot.set_state(message.from_user.id, AddProductStates.category, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data.clear()

        bot.send_message(
            message.chat.id,
            "📦 *Додавання товару*\n\nОберіть категорію:",
            reply_markup=kb.add_product_categories(categories),
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda c: c.data == "addproduct_cancel")
    def addproduct_cancel_cb(call):
        bot.answer_callback_query(call.id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, "❌ Додавання скасовано", reply_markup=kb.main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("apc_"))
    def addproduct_category(call):
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[1])
        bot.set_state(call.from_user.id, AddProductStates.name, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["category_id"] = cat_id
        bot.send_message(call.message.chat.id, "✏️ Введи назву товару:", reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.name, content_types=["text"])
    def addproduct_name(message):
        if len(message.text.strip()) < 2:
            bot.send_message(message.chat.id, "⚠️ Назва занадто коротка")
            return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["name"] = message.text.strip()
        bot.set_state(message.from_user.id, AddProductStates.description, message.chat.id)
        bot.send_message(message.chat.id, "📝 Введи опис товару:\n/skip — пропустити",
                         reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.description, content_types=["text"])
    def addproduct_description(message):
        desc = None if message.text.strip() == "/skip" else message.text.strip()
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["description"] = desc
        bot.set_state(message.from_user.id, AddProductStates.price, message.chat.id)
        bot.send_message(message.chat.id, "💰 Введи ціну (наприклад: 149.99):",
                         reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.price, content_types=["text"])
    def addproduct_price(message):
        try:
            price = float(message.text.strip().replace(",", "."))
            if price <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "⚠️ Невірна ціна. Введи число, наприклад: 149.99")
            return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["price"] = price
        bot.set_state(message.from_user.id, AddProductStates.stock, message.chat.id)
        bot.send_message(message.chat.id, "📦 Введи кількість на складі:",
                         reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.stock, content_types=["text"])
    def addproduct_stock(message):
        if not message.text.strip().isdigit() or int(message.text.strip()) < 0:
            bot.send_message(message.chat.id, "⚠️ Введи ціле число, наприклад: 10")
            return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["stock"] = int(message.text.strip())
        bot.set_state(message.from_user.id, AddProductStates.photo, message.chat.id)
        bot.send_message(message.chat.id, "🖼 Надішли фото товару:\n/skip — без фото",
                         reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.photo, content_types=["photo"])
    def addproduct_photo(message):
        _save_product(bot, message, message.photo[-1].file_id)

    @bot.message_handler(state=AddProductStates.photo, content_types=["text"])
    def addproduct_photo_skip(message):
        if message.text.strip() != "/skip":
            bot.send_message(message.chat.id, "⚠️ Надішли фото або введи /skip")
            return
        _save_product(bot, message, None)

    def _save_product(bot1, message, photo_id):
        with bot1.retrieve_data(message.from_user.id, message.chat.id) as data:
            product = db.add_product(
                category_id=data["category_id"],
                name=data["name"],
                description=data.get("description"),
                price=data["price"],
                stock=data["stock"],
                photo_id=photo_id,
            )
        bot1.delete_state(message.from_user.id, message.chat.id)
        bot1.send_message(
            message.chat.id,
            f"✅ *Товар додано!*\n\n"
            f"📦 {product.name}\n"
            f"💰 {product.price} грн\n"
            f"🗂 Залишок: {product.stock} шт.",
            parse_mode="Markdown",
            reply_markup=kb.main_menu()
        )
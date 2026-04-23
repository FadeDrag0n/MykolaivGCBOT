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

class EditProductStates(StatesGroup):
    select_product = State()
    select_field   = State()
    enter_value    = State()

class RemoveProductStates(StatesGroup):
    select_product = State()

def register(bot, admin_id):

    def is_admin(message):
        return message.from_user.id == admin_id

    def is_admin_call(call):
        return call.from_user.id == admin_id

    # ── cancel ─────────────────────────────────────────────────────────────────

    @bot.message_handler(func=lambda m: m.text == "🔙 Скасувати")
    def cancel_by_button(message):
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "❌ Скасовано", reply_markup=kb.main_menu())

    # ══════════════════════════════════════════════════════════════════════════
    # ADD PRODUCT
    # ══════════════════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════════════════
    # EDIT PRODUCT
    # ══════════════════════════════════════════════════════════════════════════

    @bot.message_handler(commands=["editproduct"])
    def editproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу")
            return
        products = db.get_all_products()
        if not products:
            bot.send_message(message.chat.id, "😔 Товарів ще немає")
            return
        bot.send_message(
            message.chat.id,
            "✏️ *Редагування товару*\n\nОберіть товар:",
            parse_mode="Markdown",
            reply_markup=kb.edit_product_list(products)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "editproduct_cancel")
    def editproduct_cancel(call):
        bot.answer_callback_query(call.id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, "❌ Редагування скасовано", reply_markup=kb.main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_p_"))
    def editproduct_select(call):
        if not is_admin_call(call):
            bot.answer_callback_query(call.id, "⛔️ Немає доступу")
            return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        if not product:
            bot.send_message(call.message.chat.id, "❌ Товар не знайдено")
            return

        text = (
            f"✏️ *{product.name}*\n\n"
            f"📄 Опис: {product.description or '—'}\n"
            f"💰 Ціна: {product.price} грн\n"
            f"📦 Залишок: {product.stock} шт.\n\n"
            "Що редагуємо?"
        )
        bot.send_message(
            call.message.chat.id, text,
            parse_mode="Markdown",
            reply_markup=kb.edit_product_fields(product_id)
        )

    # Field selection → enter value
    _FIELD_PROMPTS = {
        "name":  ("📝 Введи нову назву:", "name"),
        "desc":  ("📄 Введи новий опис (/skip — очистити):", "description"),
        "price": ("💰 Введи нову ціну (наприклад: 149.99):", "price"),
        "stock": ("📦 Введи нову кількість на складі:", "stock"),
        "photo": ("🖼 Надішли нове фото (/skip — без фото):", "photo_id"),
    }

    @bot.callback_query_handler(func=lambda c: c.data.startswith("epf_"))
    def editproduct_field(call):
        if not is_admin_call(call):
            bot.answer_callback_query(call.id, "⛔️ Немає доступу")
            return
        bot.answer_callback_query(call.id)
        parts = call.data.split("_")   # epf_name_123
        field_key = parts[1]
        product_id = int(parts[2])

        prompt, _ = _FIELD_PROMPTS.get(field_key, ("Введи нове значення:", ""))
        bot.set_state(call.from_user.id, EditProductStates.enter_value, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["edit_product_id"] = product_id
            data["edit_field_key"] = field_key

        bot.send_message(call.message.chat.id, prompt, reply_markup=kb.cancel())

    @bot.message_handler(state=EditProductStates.enter_value, content_types=["text", "photo"])
    def editproduct_save(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            product_id = data.get("edit_product_id")
            field_key  = data.get("edit_field_key")

        if not product_id or not field_key:
            bot.delete_state(message.from_user.id, message.chat.id)
            return

        product = db.get_product_by_id(product_id)
        if not product:
            bot.send_message(message.chat.id, "❌ Товар не знайдено", reply_markup=kb.main_menu())
            bot.delete_state(message.from_user.id, message.chat.id)
            return

        # Handle photo separately
        if field_key == "photo":
            if message.content_type == "photo":
                db.update_product(product_id, photo_id=message.photo[-1].file_id)
                bot.delete_state(message.from_user.id, message.chat.id)
                bot.send_message(message.chat.id, "✅ Фото оновлено!", reply_markup=kb.main_menu())
                return
            elif message.text and message.text.strip() == "/skip":
                db.update_product(product_id, photo_id=None)
                bot.delete_state(message.from_user.id, message.chat.id)
                bot.send_message(message.chat.id, "✅ Фото видалено!", reply_markup=kb.main_menu())
                return
            else:
                bot.send_message(message.chat.id, "⚠️ Надішли фото або /skip")
                return

        text = message.text.strip() if message.text else ""

        if field_key == "name":
            if len(text) < 2:
                bot.send_message(message.chat.id, "⚠️ Назва занадто коротка")
                return
            db.update_product(product_id, name=text)
            result = f"Назва: *{text}*"

        elif field_key == "desc":
            val = None if text == "/skip" else text
            db.update_product(product_id, description=val)
            result = "Опис очищено" if val is None else f"Опис: *{val}*"

        elif field_key == "price":
            try:
                price = float(text.replace(",", "."))
                if price <= 0:
                    raise ValueError
            except ValueError:
                bot.send_message(message.chat.id, "⚠️ Невірна ціна")
                return
            db.update_product(product_id, price=price)
            result = f"Ціна: *{price} грн*"

        elif field_key == "stock":
            if not text.isdigit() or int(text) < 0:
                bot.send_message(message.chat.id, "⚠️ Введи ціле число >= 0")
                return
            db.update_product(product_id, stock=int(text))
            result = f"Залишок: *{text} шт.*"
        else:
            result = "Оновлено"

        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(
            message.chat.id,
            f"✅ Товар *{product.name}* оновлено!\n{result}",
            parse_mode="Markdown",
            reply_markup=kb.main_menu()
        )

    # ══════════════════════════════════════════════════════════════════════════
    # REMOVE PRODUCT
    # ══════════════════════════════════════════════════════════════════════════

    @bot.message_handler(commands=["removeproduct"])
    def removeproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу")
            return
        products = db.get_all_products()
        if not products:
            bot.send_message(message.chat.id, "😔 Товарів ще немає")
            return
        bot.send_message(
            message.chat.id,
            "🗑 *Видалення товару*\n\nОберіть товар для видалення:",
            parse_mode="Markdown",
            reply_markup=kb.remove_product_list(products)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "removeproduct_cancel")
    def removeproduct_cancel(call):
        bot.answer_callback_query(call.id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, "❌ Видалення скасовано", reply_markup=kb.main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rm_p_"))
    def removeproduct_confirm(call):
        if not is_admin_call(call):
            bot.answer_callback_query(call.id, "⛔️ Немає доступу")
            return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        if not product:
            bot.send_message(call.message.chat.id, "❌ Товар не знайдено")
            return
        bot.send_message(
            call.message.chat.id,
            f"⚠️ Ви впевнені, що хочете видалити *{product.name}*?\n\n"
            f"💰 {product.price} грн | 📦 {product.stock} шт.\n\n"
            "Товар також буде видалено з усіх кошиків.",
            parse_mode="Markdown",
            reply_markup=kb.confirm_remove(product_id)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rm_confirm_"))
    def removeproduct_do(call):
        if not is_admin_call(call):
            bot.answer_callback_query(call.id, "⛔️ Немає доступу")
            return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        name = product.name if product else "Товар"
        db.delete_product(product_id)
        bot.send_message(
            call.message.chat.id,
            f"✅ Товар *{name}* видалено!",
            parse_mode="Markdown",
            reply_markup=kb.main_menu()
        )
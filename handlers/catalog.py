import ua
import keyboards as kb
import db

def register(bot):

    def _ensure_categories():
        """Seed default categories if db is empty."""
        categories = db.get_categories()
        if not categories:
            db.add_category("Корм", "animals")
            db.add_category("Аксесуари", "animals")
            db.add_category("Добрива", "plants")
            db.add_category("Ґрунти", "plants")

    # ── main catalog entry ─────────────────────────────────────────────────────

    @bot.message_handler(commands=["catalog"])
    @bot.message_handler(func=lambda m: m.text == "🌿 Каталог товарів")
    def catalog(message):
        _ensure_categories()
        bot.send_message(message.chat.id, ua.CATALOG_OPEN, reply_markup=kb.category())

    @bot.callback_query_handler(func=lambda c: c.data == "catalog_back_main")
    def catalog_back_main(call):
        bot.answer_callback_query(call.id)
        _ensure_categories()
        bot.send_message(call.message.chat.id, ua.CATALOG_OPEN, reply_markup=kb.category())

    # ── type → subcategories ───────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data == "cat_animals")
    def animals(call):
        bot.answer_callback_query(call.id)
        _show_subcategories(call, "animals", "🐾 Товари для тварин")

    @bot.callback_query_handler(func=lambda c: c.data == "cat_plants")
    def plants(call):
        bot.answer_callback_query(call.id)
        _show_subcategories(call, "plants", "🌿 Товари для рослин")

    def _show_subcategories(call, cat_type: str, title: str):
        cats = db.get_categories(cat_type)
        if not cats:
            bot.send_message(call.message.chat.id, "😔 Категорій ще немає")
            return
        bot.send_message(
            call.message.chat.id,
            f"{title}\n\nОберіть підкатегорію:",
            reply_markup=kb.subcategories(cats, cat_type)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "catalog_back")
    def back_to_catalog(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, ua.CATALOG_OPEN, reply_markup=kb.category())

    # ── subcategory → product list ─────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("subcat_"))
    def show_products(call):
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[1])
        category = db.get_category(cat_id)
        products = db.get_products(cat_id)

        if not products:
            bot.send_message(
                call.message.chat.id,
                "😔 У цій категорії ще немає товарів",
                reply_markup=kb.subcategories(db.get_categories(category.type if category else None), "")
            )
            return

        bot.send_message(
            call.message.chat.id,
            f"📦 *{category.name if category else 'Товари'}* — {len(products)} позицій\n\nОберіть товар:",
            parse_mode="Markdown"
        )
        for product in products:
            _send_product_card(bot, call.message.chat.id, product, call.from_user.id)

    # ── product card ───────────────────────────────────────────────────────────

    def _send_product_card(bot1, chat_id: int, product, tg_id: int):
        cart_item = db.cart_item_get(tg_id, product.id)
        in_cart = cart_item is not None

        stock_text = f"✅ В наявності: {product.stock} шт." if product.stock > 0 else "❌ Немає в наявності"
        desc_text = f"\n📄 {product.description}" if product.description else ""
        cart_text = f"\n🛒 У кошику: {cart_item.quantity} шт." if in_cart else ""

        caption = (
            f"📦 *{product.name}*{desc_text}\n\n"
            f"💰 Ціна: *{product.price} грн*\n"
            f"{stock_text}{cart_text}"
        )

        markup = kb.product_card(product.id, in_cart=in_cart)

        if product.photo_id:
            bot1.send_photo(
                chat_id,
                product.photo_id,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            bot1.send_message(
                chat_id,
                caption,
                parse_mode="Markdown",
                reply_markup=markup
            )

    # ── add to cart ────────────────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cart_add_"))
    def cart_add(call):
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)

        if not product or product.stock == 0:
            bot.answer_callback_query(call.id, "❌ Товар недоступний", show_alert=True)
            return

        # Check existing qty
        item = db.cart_item_get(call.from_user.id, product_id)
        current_qty = item.quantity if item else 0

        # Add 1 by default, then show qty picker
        new_qty = current_qty + 1
        db.cart_set_quantity(call.from_user.id, product_id, new_qty)

        bot.send_message(
            call.message.chat.id,
            f"🛒 *{product.name}*\n\nОберіть кількість:",
            parse_mode="Markdown",
            reply_markup=kb.cart_item_actions(product_id, new_qty)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cart_qty_"))
    def cart_change_qty(call):
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        item = db.cart_item_get(call.from_user.id, product_id)
        qty = item.quantity if item else 1

        bot.send_message(
            call.message.chat.id,
            f"🛒 *{product.name}*\n\nЗмінити кількість:",
            parse_mode="Markdown",
            reply_markup=kb.cart_item_actions(product_id, qty)
        )

    def _safe_edit_qty_markup(call, product_id: int, qty: int):
        """Edit the quantity picker markup, ignoring 'message not found' errors."""
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=kb.cart_item_actions(product_id, qty)
            )
        except Exception as e:
            if "message to edit not found" in str(e).lower() or "message is not modified" in str(e).lower():
                pass  # повідомлення вже видалено або не змінилось — ігноруємо
            else:
                raise

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cqty_plus_"))
    def cqty_plus(call):
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        item = db.cart_item_get(call.from_user.id, product_id)
        qty = (item.quantity if item else 0) + 1

        if product and qty > product.stock:
            bot.answer_callback_query(call.id, f"⚠️ Максимум {product.stock} шт.", show_alert=True)
            return

        db.cart_set_quantity(call.from_user.id, product_id, qty)
        bot.answer_callback_query(call.id)
        _safe_edit_qty_markup(call, product_id, qty)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cqty_minus_"))
    def cqty_minus(call):
        product_id = int(call.data.split("_")[2])
        item = db.cart_item_get(call.from_user.id, product_id)
        qty = max(1, (item.quantity if item else 1) - 1)

        db.cart_set_quantity(call.from_user.id, product_id, qty)
        bot.answer_callback_query(call.id)
        _safe_edit_qty_markup(call, product_id, qty)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cqty_remove_"))
    def cqty_remove(call):
        product_id = int(call.data.split("_")[2])
        db.cart_remove(call.from_user.id, product_id)
        bot.answer_callback_query(call.id, "🗑 Видалено з кошика")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cqty_done_"))
    def cqty_done(call):
        product_id = int(call.data.split("_")[2])
        item = db.cart_item_get(call.from_user.id, product_id)
        product = db.get_product_by_id(product_id)
        qty = item.quantity if item else 0

        bot.answer_callback_query(call.id, f"✅ {product.name} × {qty} — збережено")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("back_to_subcat_"))
    def back_to_subcat(call):
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[3])
        product = db.get_product_by_id(product_id)
        if not product:
            return
        category = db.get_category(product.category_id)
        if not category:
            return
        cats = db.get_categories(category.type)
        bot.send_message(
            call.message.chat.id,
            f"{'🐾 Товари для тварин' if category.type == 'animals' else '🌿 Товари для рослин'}\n\nОберіть підкатегорію:",
            reply_markup=kb.subcategories(cats, category.type)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "noop")
    def noop(call):
        bot.answer_callback_query(call.id)
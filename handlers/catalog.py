import ua
import keyboards as kb
import db
from keyboards import CATALOG_PAGE_SIZE
from telebot.handler_backends import State, StatesGroup

class SearchStates(StatesGroup):
    waiting_query = State()

def register(bot):

    def _ensure_categories():
        categories = db.get_categories()
        if not categories:
            db.add_category("Корм", "animals")
            db.add_category("Аксесуари", "animals")
            db.add_category("Добрива", "plants")
            db.add_category("Ґрунти", "plants")

    # ── Пошук ─────────────────────────────────────────────────────────────────

    @bot.message_handler(commands=["search"])
    @bot.message_handler(func=lambda m: m.text == "🔍 Пошук товарів")
    def search_start(message):
        bot.set_state(message.from_user.id, SearchStates.waiting_query, message.chat.id)
        bot.send_message(
            message.chat.id,
            "🔍 Введи назву або частину назви товару:",
            reply_markup=kb.cancel()
        )

    @bot.message_handler(state=SearchStates.waiting_query, content_types=["text"])
    def search_query(message):
        query = message.text.strip()
        bot.delete_state(message.from_user.id, message.chat.id)

        products = db.search_products(query)
        if not products:
            bot.send_message(
                message.chat.id,
                f"😔 За запитом *«{query}»* нічого не знайдено\n\nСпробуй інший запит або перегляньте каталог.",
                parse_mode="Markdown",
                reply_markup=kb.main_menu()
            )
            return

        bot.send_message(
            message.chat.id,
            f"🔍 За запитом *«{query}»* знайдено: {len(products)} товар(ів)\n\n"
            f"{'Показую перші 5:' if len(products) > 5 else ''}",
            parse_mode="Markdown",
            reply_markup=kb.main_menu()
        )
        for product in products[:5]:
            _send_product_card(bot, message.chat.id, product, message.from_user.id)

    # ── Головна сторінка каталогу ──────────────────────────────────────────────

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

    # ── Тип → підкатегорії ─────────────────────────────────────────────────────

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

    # Повернення до підкатегорій за cat_id (з пагінації)
    @bot.callback_query_handler(func=lambda c: c.data.startswith("back_subcat_cat_"))
    def back_subcat_from_page(call):
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[3])
        category = db.get_category(cat_id)
        if not category:
            return
        cats = db.get_categories(category.type)
        title = "🐾 Товари для тварин" if category.type == "animals" else "🌿 Товари для рослин"
        bot.send_message(
            call.message.chat.id,
            f"{title}\n\nОберіть підкатегорію:",
            reply_markup=kb.subcategories(cats, category.type)
        )

    # ── Підкатегорія → список товарів (сторінка 0) ────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("subcat_"))
    def show_products(call):
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[1])
        _show_product_page(call.message.chat.id, call.from_user.id, cat_id, page=0, sort="default")

    # ── Фільтр/сортування ─────────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("catsort_"))
    def catalog_sort(call):
        bot.answer_callback_query(call.id)
        # catsort_{cat_id}_{sort}
        parts = call.data.split("_", 2)
        cat_id = int(parts[1])
        sort = parts[2]
        _show_product_page(call.message.chat.id, call.from_user.id, cat_id, page=0, sort=sort)

    # ── Пагінація ──────────────────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("catpage_"))
    def catalog_page(call):
        bot.answer_callback_query(call.id)
        # catpage_{cat_id}_{page}_{sort}
        parts = call.data.split("_", 3)
        cat_id = int(parts[1])
        page = int(parts[2])
        sort = parts[3] if len(parts) > 3 else "default"
        _show_product_page(call.message.chat.id, call.from_user.id, cat_id, page=page, sort=sort)

    def _show_product_page(chat_id: int, tg_id: int, cat_id: int, page: int, sort: str):
        category = db.get_category(cat_id)
        products = db.get_products(cat_id, sort=sort)

        if not products:
            bot.send_message(
                chat_id,
                "😔 У цій категорії ще немає товарів",
                reply_markup=kb.subcategories(
                    db.get_categories(category.type if category else None), ""
                )
            )
            return

        total = len(products)
        start = page * CATALOG_PAGE_SIZE
        page_products = products[start:start + CATALOG_PAGE_SIZE]
        cat_name = category.name if category else "Товари"

        sort_labels = {
            "default":    "за замовч.",
            "price_asc":  "ціна ↑",
            "price_desc": "ціна ↓",
            "in_stock":   "в наявності",
        }

        # Заголовок із фільтрами
        bot.send_message(
            chat_id,
            f"📦 *{cat_name}* — {total} позицій\n"
            f"Сортування: _{sort_labels.get(sort, sort)}_\n\n"
            f"Сторінка {page + 1}/{(total - 1) // CATALOG_PAGE_SIZE + 1}  •  "
            f"Показано {start + 1}–{min(start + CATALOG_PAGE_SIZE, total)}",
            parse_mode="Markdown",
            reply_markup=kb.catalog_filters(cat_id, current_sort=sort)
        )

        for product in page_products:
            _send_product_card(bot, chat_id, product, tg_id)

        # Навігація (тільки якщо є більше однієї сторінки)
        if total > CATALOG_PAGE_SIZE:
            bot.send_message(
                chat_id,
                "⬆️ Навігація:",
                reply_markup=kb.catalog_pagination(cat_id, page, total, sort)
            )

    # ── Картка товару ──────────────────────────────────────────────────────────

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
            bot1.send_photo(chat_id, product.photo_id, caption=caption,
                            parse_mode="Markdown", reply_markup=markup)
        else:
            bot1.send_message(chat_id, caption, parse_mode="Markdown", reply_markup=markup)

    # ── Додати у кошик ────────────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cart_add_"))
    def cart_add(call):
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)

        if not product or product.stock == 0:
            bot.answer_callback_query(call.id, "❌ Товар недоступний", show_alert=True)
            return

        item = db.cart_item_get(call.from_user.id, product_id)
        current_qty = item.quantity if item else 0
        new_qty = current_qty + 1

        if new_qty > product.stock:
            bot.answer_callback_query(call.id, f"⚠️ Максимум {product.stock} шт.", show_alert=True)
            return

        db.cart_set_quantity(call.from_user.id, product_id, new_qty)
        bot.answer_callback_query(call.id)
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
        try:
            bot.edit_message_reply_markup(
                call.message.chat.id, call.message.message_id,
                reply_markup=kb.cart_item_actions(product_id, qty)
            )
        except Exception as e:
            err = str(e).lower()
            if "message to edit not found" in err or "message is not modified" in err:
                pass
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
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cqty_done_"))
    def cqty_done(call):
        product_id = int(call.data.split("_")[2])
        item = db.cart_item_get(call.from_user.id, product_id)
        product = db.get_product_by_id(product_id)
        qty = item.quantity if item else 0
        bot.answer_callback_query(call.id, f"✅ {product.name} × {qty} — збережено")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

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
        title = "🐾 Товари для тварин" if category.type == "animals" else "🌿 Товари для рослин"
        bot.send_message(
            call.message.chat.id,
            f"{title}\n\nОберіть підкатегорію:",
            reply_markup=kb.subcategories(cats, category.type)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "noop")
    def noop(call):
        bot.answer_callback_query(call.id)
import db
import keyboards as kb
from models import ORDER_STATUS_LABELS, OrderStatus, ACTIVE_STATUSES
from telebot.handler_backends import State, StatesGroup


class AddProductStates(StatesGroup):
    category    = State()
    name        = State()
    description = State()
    price       = State()
    stock       = State()
    photo       = State()

class EditProductStates(StatesGroup):
    enter_value = State()

class AdminCatStates(StatesGroup):
    add_name    = State()
    add_type    = State()
    rename      = State()

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
    # /admin — головна панель
    # ══════════════════════════════════════════════════════════════════════════

    @bot.message_handler(commands=["admin"])
    def admin_panel(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу")
            return
        bot.send_message(
            message.chat.id,
            "🔧 *Панель адміністратора*\n\nОберіть розділ:",
            parse_mode="Markdown",
            reply_markup=kb.admin_panel()
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_back")
    def adm_back(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔧 *Панель адміністратора*\n\nОберіть розділ:",
                         parse_mode="Markdown", reply_markup=kb.admin_panel())

    # ══════════════════════════════════════════════════════════════════════════
    # Категорії
    # ══════════════════════════════════════════════════════════════════════════

    @bot.callback_query_handler(func=lambda c: c.data == "adm_categories")
    def adm_categories(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        _show_admin_categories(call.message.chat.id)

    def _show_admin_categories(chat_id: int):
        cats = db.get_categories()
        bot.send_message(
            chat_id,
            "🗂 *Категорії*\n\nОберіть категорію для редагування або додайте нову:",
            parse_mode="Markdown",
            reply_markup=kb.admin_categories(cats)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_") and not c.data.startswith("adm_cat_add") and not c.data.startswith("adm_cat_rename") and not c.data.startswith("adm_cat_del") and not c.data.startswith("adm_cat_type"))
    def adm_cat_select(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[2])
        cat = db.get_category(cat_id)
        if not cat:
            bot.send_message(call.message.chat.id, "❌ Категорію не знайдено")
            return
        icon = "🐾" if cat.type == "animals" else "🌿"
        bot.send_message(
            call.message.chat.id,
            f"{icon} *{cat.name}*\nТип: {'Тварини' if cat.type == 'animals' else 'Рослини'}",
            parse_mode="Markdown",
            reply_markup=kb.admin_category_actions(cat_id)
        )

    # Додати категорію
    @bot.callback_query_handler(func=lambda c: c.data == "adm_cat_add")
    def adm_cat_add(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, AdminCatStates.add_name, call.message.chat.id)
        bot.send_message(call.message.chat.id, "📝 Введи назву нової категорії:", reply_markup=kb.cancel())

    @bot.message_handler(state=AdminCatStates.add_name, content_types=["text"])
    def adm_cat_add_name(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["new_cat_name"] = message.text.strip()
        bot.set_state(message.from_user.id, AdminCatStates.add_type, message.chat.id)
        bot.send_message(message.chat.id, "Оберіть тип категорії:", reply_markup=kb.admin_cat_type())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_type_"))
    def adm_cat_type_select(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_type = call.data.split("_")[3]  # animals / plants
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            name = data.get("new_cat_name", "Нова категорія")
        db.add_category(name, cat_type)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        icon = "🐾" if cat_type == "animals" else "🌿"
        bot.send_message(call.message.chat.id, f"✅ Категорію *{icon} {name}* додано!", parse_mode="Markdown")
        _show_admin_categories(call.message.chat.id)

    # Перейменувати
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_rename_"))
    def adm_cat_rename(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[3])
        bot.set_state(call.from_user.id, AdminCatStates.rename, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["rename_cat_id"] = cat_id
        bot.send_message(call.message.chat.id, "✏️ Введи нову назву категорії:", reply_markup=kb.cancel())

    @bot.message_handler(state=AdminCatStates.rename, content_types=["text"])
    def adm_cat_rename_save(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            cat_id = data.get("rename_cat_id")
        db.update_category(cat_id, name=message.text.strip())
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, f"✅ Назву змінено на *{message.text.strip()}*", parse_mode="Markdown")
        _show_admin_categories(message.chat.id)

    # Видалити
    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_del_") and "confirm" not in c.data)
    def adm_cat_del(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[3])
        cat = db.get_category(cat_id)
        if not cat:
            return
        bot.send_message(
            call.message.chat.id,
            f"⚠️ Видалити категорію *{cat.name}*?\n\nУсі товари цієї категорії залишаться без категорії.",
            parse_mode="Markdown",
            reply_markup=kb.admin_confirm_cat_del(cat_id)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_del_confirm_"))
    def adm_cat_del_confirm(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[4])
        cat = db.get_category(cat_id)
        name = cat.name if cat else "категорію"
        db.delete_category(cat_id)
        bot.send_message(call.message.chat.id, f"✅ *{name}* видалено", parse_mode="Markdown")
        _show_admin_categories(call.message.chat.id)

    # ══════════════════════════════════════════════════════════════════════════
    # Користувачі
    # ══════════════════════════════════════════════════════════════════════════

    @bot.callback_query_handler(func=lambda c: c.data == "adm_users")
    def adm_users(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        _show_users_page(call.message.chat.id, 0)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_users_page_"))
    def adm_users_page(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        page = int(call.data.split("_")[3])
        _show_users_page(call.message.chat.id, page)

    def _show_users_page(chat_id: int, page: int):
        users = db.get_all_users()
        bot.send_message(
            chat_id,
            f"👥 *Користувачі* — {len(users)} осіб\nСторінка {page + 1}:",
            parse_mode="Markdown",
            reply_markup=kb.admin_users_list(users, page)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_user_"))
    def adm_user_card(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        tg_id = int(call.data.split("_")[2])
        user = db.get_user(tg_id)
        if not user:
            bot.send_message(call.message.chat.id, "❌ Користувача не знайдено")
            return

        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"
        username = f"@{user.username}" if user.username else "—"
        done_orders = db.count_user_orders(tg_id)
        cart_items = db.cart_get(tg_id)

        cart_text = ""
        if cart_items:
            cart_lines = [f"  • {i.product_name} × {i.quantity}" for i in cart_items]
            cart_text = "\n🛒 Кошик:\n" + "\n".join(cart_lines)
        else:
            cart_text = "\n🛒 Кошик порожній"

        text = (
            f"👤 *Картка користувача*\n\n"
            f"🙍 Ім'я: {name}\n"
            f"💬 Telegram: {username}\n"
            f"🆔 ID: `{tg_id}`\n"
            f"📱 Телефон: {user.phone or '—'}\n"
            f"📧 Email: {user.email or '—'}\n"
            f"🏠 Адреса: {user.address or '—'}\n"
            f"✅ Виконаних замовлень: {done_orders}\n"
            f"📅 Зареєстрований: {(user.created_at or '')[:10]}"
            f"{cart_text}"
        )

        # Спробуємо отримати фото профілю
        try:
            photos = bot.get_user_profile_photos(tg_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                bot.send_photo(call.message.chat.id, file_id, caption=text, parse_mode="Markdown")
                return
        except Exception:
            pass

        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    # ══════════════════════════════════════════════════════════════════════════
    # Замовлення
    # ══════════════════════════════════════════════════════════════════════════

    @bot.callback_query_handler(func=lambda c: c.data == "adm_orders_active")
    def adm_orders_active(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        _show_orders(call.message.chat.id, active_only=True)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_orders_all")
    def adm_orders_all(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        _show_orders(call.message.chat.id, active_only=False)

    def _show_orders(chat_id: int, active_only: bool):
        orders = db.get_all_orders(active_only=active_only)
        title = "🔔 Активні замовлення" if active_only else "📋 Всі замовлення"
        if not orders:
            bot.send_message(chat_id, f"{title}\n\n😔 Замовлень немає", reply_markup=kb.admin_panel())
            return
        bot.send_message(chat_id, f"{title} — *{len(orders)}* шт.", parse_mode="Markdown")
        for order in orders[:15]:
            _send_admin_order_card(bot, chat_id, order)

    def _send_admin_order_card(bot1, chat_id: int, order):
        try:
            status_obj = OrderStatus(order.status)
            status_label = ORDER_STATUS_LABELS.get(status_obj, order.status)
        except ValueError:
            status_label = order.status

        name = f"{order.first_name or ''} {order.last_name or ''}".strip() or "—"
        username = f"@{order.username}" if order.username else "—"
        lines = [f"• {i.product_name} × {i.quantity} — {i.price * i.quantity:.2f} грн" for i in order.items]
        created = order.created_at[:16] if order.created_at else "—"

        text = (
            f"🔖 *Замовлення #{order.id}*\n"
            f"📅 {created}\n"
            f"📊 {status_label}\n\n"
            f"👤 {name} ({username})\n"
            f"🆔 `{order.tg_id}`\n"
            f"📱 {order.phone}\n"
            + (f"🏠 {order.address}\n" if order.address else "")
            + "\n📦 Товари:\n" + "\n".join(lines)
            + f"\n\n💰 *{order.total:.2f} грн*"
        )
        bot1.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb.admin_order_card(order.id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ord_change_"))
    def adm_ord_change_status(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        order_id = int(call.data.split("_")[3])
        order = db.get_order(order_id)
        if not order:
            bot.send_message(call.message.chat.id, "❌ Замовлення не знайдено")
            return
        bot.send_message(
            call.message.chat.id,
            f"🔄 Замовлення *#{order_id}* — оберіть новий статус:",
            parse_mode="Markdown",
            reply_markup=kb.admin_order_statuses(order_id, order.status)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ord_status_"))
    def adm_ord_set_status(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        parts = call.data.split("_")
        # adm_ord_status_{order_id}_{status_value}
        # status може мати підкреслення (in_progress) — беремо все після 4-го елементу
        order_id = int(parts[3])
        new_status = "_".join(parts[4:])
        db.update_order_status(order_id, new_status)

        try:
            status_label = ORDER_STATUS_LABELS[OrderStatus(new_status)]
        except Exception:
            status_label = new_status

        bot.send_message(
            call.message.chat.id,
            f"✅ Статус замовлення *#{order_id}* змінено на:\n{status_label}",
            parse_mode="Markdown",
            reply_markup=kb.admin_panel()
        )

        # Повідомляємо клієнта
        order = db.get_order(order_id)
        if order:
            try:
                bot.send_message(
                    order.tg_id,
                    f"🔔 *Статус вашого замовлення #{order_id} оновлено!*\n\n"
                    f"📊 Новий статус: {status_label}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass  # користувач міг заблокувати бота

    # ══════════════════════════════════════════════════════════════════════════
    # Статистика (через /admin → кнопка)
    # ══════════════════════════════════════════════════════════════════════════

    @bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
    def adm_stats(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        s = db.get_stats()
        top_rev = (
            f"*{s['top_revenue_product'][0]}* — {s['top_revenue_product'][1]:.2f} грн"
            if s['top_revenue_product'] else "—"
        )
        top_qty = (
            f"*{s['top_qty_product'][0]}* — {s['top_qty_product'][1]} шт."
            if s['top_qty_product'] else "—"
        )
        text = (
            "📊 *Статистика магазину*\n\n"
            "💰 *Заробіток*\n"
            f"├ За цей місяць: *{s['revenue_month']:.2f} грн*\n"
            f"└ За весь час: *{s['revenue_all']:.2f} грн*\n\n"
            "📦 *Замовлення*\n"
            f"├ За цей місяць: *{s['orders_month']}*\n"
            f"└ За весь час: *{s['orders_all']}*\n\n"
            "🏆 *Топ товари (виконані замовлення)*\n"
            f"├ За виручкою: {top_rev}\n"
            f"└ За кількістю: {top_qty}"
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=kb.admin_panel())

    # ══════════════════════════════════════════════════════════════════════════
    # Товари (швидкі посилання з панелі)
    # ══════════════════════════════════════════════════════════════════════════

    @bot.callback_query_handler(func=lambda c: c.data == "adm_products")
    def adm_products(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "📦 *Управління товарами*\n\n"
            "Використовуй команди:\n"
            "/addproduct — додати товар\n"
            "/editproduct — редагувати товар\n"
            "/removeproduct — видалити товар",
            parse_mode="Markdown",
            reply_markup=kb.admin_panel()
        )

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
            message.chat.id, "📦 *Додавання товару*\n\nОберіть категорію:",
            reply_markup=kb.add_product_categories(categories), parse_mode="Markdown"
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
        bot.send_message(message.chat.id, "📝 Введи опис:\n/skip — пропустити", reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.description, content_types=["text"])
    def addproduct_description(message):
        desc = None if message.text.strip() == "/skip" else message.text.strip()
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["description"] = desc
        bot.set_state(message.from_user.id, AddProductStates.price, message.chat.id)
        bot.send_message(message.chat.id, "💰 Введи ціну:", reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.price, content_types=["text"])
    def addproduct_price(message):
        try:
            price = float(message.text.strip().replace(",", "."))
            if price <= 0: raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "⚠️ Невірна ціна")
            return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["price"] = price
        bot.set_state(message.from_user.id, AddProductStates.stock, message.chat.id)
        bot.send_message(message.chat.id, "📦 Введи кількість на складі:", reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.stock, content_types=["text"])
    def addproduct_stock(message):
        if not message.text.strip().isdigit() or int(message.text.strip()) < 0:
            bot.send_message(message.chat.id, "⚠️ Введи ціле число")
            return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["stock"] = int(message.text.strip())
        bot.set_state(message.from_user.id, AddProductStates.photo, message.chat.id)
        bot.send_message(message.chat.id, "🖼 Надішли фото:\n/skip — без фото", reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.photo, content_types=["photo"])
    def addproduct_photo(message):
        _save_product(bot, message, message.photo[-1].file_id)

    @bot.message_handler(state=AddProductStates.photo, content_types=["text"])
    def addproduct_photo_skip(message):
        if message.text.strip() != "/skip":
            bot.send_message(message.chat.id, "⚠️ Надішли фото або /skip")
            return
        _save_product(bot, message, None)

    def _save_product(bot1, message, photo_id):
        with bot1.retrieve_data(message.from_user.id, message.chat.id) as data:
            product = db.add_product(
                category_id=data["category_id"], name=data["name"],
                description=data.get("description"), price=data["price"],
                stock=data["stock"], photo_id=photo_id,
            )
        bot1.delete_state(message.from_user.id, message.chat.id)
        bot1.send_message(
            message.chat.id,
            f"✅ *Товар додано!*\n\n📦 {product.name}\n💰 {product.price} грн\n🗂 {product.stock} шт.",
            parse_mode="Markdown", reply_markup=kb.main_menu()
        )

    # ══════════════════════════════════════════════════════════════════════════
    # EDIT PRODUCT
    # ══════════════════════════════════════════════════════════════════════════

    @bot.message_handler(commands=["editproduct"])
    def editproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу"); return
        products = db.get_all_products()
        if not products:
            bot.send_message(message.chat.id, "😔 Товарів ще немає"); return
        bot.send_message(message.chat.id, "✏️ *Редагування товару*\n\nОберіть товар:",
                         parse_mode="Markdown", reply_markup=kb.edit_product_list(products))

    @bot.callback_query_handler(func=lambda c: c.data == "editproduct_cancel")
    def editproduct_cancel(call):
        bot.answer_callback_query(call.id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, "❌ Скасовано", reply_markup=kb.main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("edit_p_"))
    def editproduct_select(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        if not product:
            bot.send_message(call.message.chat.id, "❌ Не знайдено"); return
        text = (f"✏️ *{product.name}*\n📄 {product.description or '—'}\n"
                f"💰 {product.price} грн | 📦 {product.stock} шт.\n\nЩо змінюємо?")
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown",
                         reply_markup=kb.edit_product_fields(product_id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("epf_"))
    def editproduct_field(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        parts = call.data.split("_")
        field_key, product_id = parts[1], int(parts[2])
        prompts = {
            "name": "📝 Введи нову назву:",
            "desc": "📄 Введи новий опис (/skip — очистити):",
            "price": "💰 Введи нову ціну:",
            "stock": "📦 Введи нову кількість:",
            "photo": "🖼 Надішли нове фото (/skip — без фото):",
        }
        bot.set_state(call.from_user.id, EditProductStates.enter_value, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["edit_product_id"] = product_id
            data["edit_field_key"] = field_key
        bot.send_message(call.message.chat.id, prompts.get(field_key, "Введи значення:"), reply_markup=kb.cancel())

    @bot.message_handler(state=EditProductStates.enter_value, content_types=["text", "photo"])
    def editproduct_save(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            product_id = data.get("edit_product_id")
            field_key  = data.get("edit_field_key")
        product = db.get_product_by_id(product_id)
        if not product:
            bot.delete_state(message.from_user.id, message.chat.id); return

        if field_key == "photo":
            if message.content_type == "photo":
                db.update_product(product_id, photo_id=message.photo[-1].file_id)
                bot.delete_state(message.from_user.id, message.chat.id)
                bot.send_message(message.chat.id, "✅ Фото оновлено!", reply_markup=kb.main_menu()); return
            elif message.text and message.text.strip() == "/skip":
                db.update_product(product_id, photo_id=None)
                bot.delete_state(message.from_user.id, message.chat.id)
                bot.send_message(message.chat.id, "✅ Фото видалено!", reply_markup=kb.main_menu()); return
            else:
                bot.send_message(message.chat.id, "⚠️ Надішли фото або /skip"); return

        text = message.text.strip() if message.text else ""
        if field_key == "name":
            if len(text) < 2:
                bot.send_message(message.chat.id, "⚠️ Занадто коротко"); return
            db.update_product(product_id, name=text); result = f"Назва: *{text}*"
        elif field_key == "desc":
            val = None if text == "/skip" else text
            db.update_product(product_id, description=val)
            result = "Опис очищено" if val is None else f"Опис оновлено"
        elif field_key == "price":
            try:
                price = float(text.replace(",", "."))
                if price <= 0: raise ValueError
            except ValueError:
                bot.send_message(message.chat.id, "⚠️ Невірна ціна"); return
            db.update_product(product_id, price=price); result = f"Ціна: *{price} грн*"
        elif field_key == "stock":
            if not text.isdigit() or int(text) < 0:
                bot.send_message(message.chat.id, "⚠️ Введи ціле число >= 0"); return
            db.update_product(product_id, stock=int(text)); result = f"Залишок: *{text} шт.*"
        else:
            result = "Оновлено"

        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, f"✅ *{product.name}* оновлено!\n{result}",
                         parse_mode="Markdown", reply_markup=kb.main_menu())

    # ══════════════════════════════════════════════════════════════════════════
    # REMOVE PRODUCT
    # ══════════════════════════════════════════════════════════════════════════

    @bot.message_handler(commands=["removeproduct"])
    def removeproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу"); return
        products = db.get_all_products()
        if not products:
            bot.send_message(message.chat.id, "😔 Товарів ще немає"); return
        bot.send_message(message.chat.id, "🗑 *Видалення товару*\n\nОберіть товар:",
                         parse_mode="Markdown", reply_markup=kb.remove_product_list(products))

    @bot.callback_query_handler(func=lambda c: c.data == "removeproduct_cancel")
    def removeproduct_cancel(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "❌ Скасовано", reply_markup=kb.main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rm_p_"))
    def removeproduct_confirm(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        if not product:
            bot.send_message(call.message.chat.id, "❌ Не знайдено"); return
        bot.send_message(
            call.message.chat.id,
            f"⚠️ Видалити *{product.name}*?\n💰 {product.price} грн | 📦 {product.stock} шт.",
            parse_mode="Markdown", reply_markup=kb.confirm_remove(product_id)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rm_confirm_"))
    def removeproduct_do(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        name = product.name if product else "Товар"
        db.delete_product(product_id)
        bot.send_message(call.message.chat.id, f"✅ *{name}* видалено!", parse_mode="Markdown",
                         reply_markup=kb.main_menu())
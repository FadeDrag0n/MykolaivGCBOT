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
    add_name = State()
    add_type = State()
    rename   = State()

class AdminTTNState(StatesGroup):
    waiting_ttn = State()

class BroadcastState(StatesGroup):
    waiting_text  = State()
    waiting_media = State()
    confirm       = State()

def register(bot, admin_id):

    def is_admin(message):
        return message.from_user.id == admin_id

    def is_admin_call(call):
        return call.from_user.id == admin_id

    @bot.message_handler(func=lambda m: m.text == "🔙 Скасувати")
    def cancel_by_button(message):
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "❌ Скасовано", reply_markup=kb.main_menu())

    @bot.message_handler(commands=["admin"])
    def admin_panel_cmd(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу"); return
        bot.send_message(message.chat.id, "🔧 *Панель адміністратора*\n\nОберіть розділ:",
                         parse_mode="Markdown", reply_markup=kb.admin_panel())

    @bot.callback_query_handler(func=lambda c: c.data == "adm_back")
    def adm_back(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🔧 *Панель адміністратора*\n\nОберіть розділ:",
                         parse_mode="Markdown", reply_markup=kb.admin_panel())

    @bot.callback_query_handler(func=lambda c: c.data == "adm_categories")
    def adm_categories(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        _show_admin_categories(call.message.chat.id)

    def _show_admin_categories(chat_id):
        cats = db.get_categories()
        bot.send_message(chat_id, "🗂 *Категорії*\n\nОберіть для редагування або додайте нову:",
                         parse_mode="Markdown", reply_markup=kb.admin_categories(cats))

    @bot.callback_query_handler(func=lambda c: (
        c.data.startswith("adm_cat_") and
        not any(c.data.startswith(x) for x in
                ["adm_cat_add","adm_cat_rename","adm_cat_del","adm_cat_type"])
    ))
    def adm_cat_select(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[2])
        cat = db.get_category(cat_id)
        if not cat: return
        icon = "🐾" if cat.type == "animals" else "🌿"
        bot.send_message(call.message.chat.id,
            f"{icon} *{cat.name}*\nТип: {'Тварини' if cat.type=='animals' else 'Рослини'}",
            parse_mode="Markdown", reply_markup=kb.admin_category_actions(cat_id))

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
        bot.send_message(message.chat.id, "Оберіть тип:", reply_markup=kb.admin_cat_type())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_type_"))
    def adm_cat_type_select(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_type = call.data.split("_")[3]
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            name = data.get("new_cat_name", "Нова")
        db.add_category(name, cat_type)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        icon = "🐾" if cat_type == "animals" else "🌿"
        bot.send_message(call.message.chat.id, f"✅ *{icon} {name}* додано!", parse_mode="Markdown")
        _show_admin_categories(call.message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_rename_"))
    def adm_cat_rename(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[3])
        bot.set_state(call.from_user.id, AdminCatStates.rename, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["rename_cat_id"] = cat_id
        bot.send_message(call.message.chat.id, "✏️ Введи нову назву:", reply_markup=kb.cancel())

    @bot.message_handler(state=AdminCatStates.rename, content_types=["text"])
    def adm_cat_rename_save(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            cat_id = data.get("rename_cat_id")
        db.update_category(cat_id, name=message.text.strip())
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, f"✅ Назву змінено на *{message.text.strip()}*",
                         parse_mode="Markdown")
        _show_admin_categories(message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_cat_del_") and "confirm" not in c.data)
    def adm_cat_del(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        cat_id = int(call.data.split("_")[3])
        cat = db.get_category(cat_id)
        if not cat: return
        bot.send_message(call.message.chat.id,
            f"⚠️ Видалити *{cat.name}*?", parse_mode="Markdown",
            reply_markup=kb.admin_confirm_cat_del(cat_id))

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

    def _show_users_page(chat_id, page):
        users = db.get_all_users()
        bot.send_message(chat_id, f"👥 *Користувачі* — {len(users)} осіб\nСторінка {page+1}:",
                         parse_mode="Markdown", reply_markup=kb.admin_users_list(users, page))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_user_"))
    def adm_user_card(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        tg_id = int(call.data.split("_")[2])
        user = db.get_user(tg_id)
        if not user: return
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "—"
        username = f"@{user.username}" if user.username else "—"
        done_orders = db.count_user_orders(tg_id)
        cart_items = db.cart_get(tg_id)
        cart_text = ("\n🛒 Кошик:\n" + "\n".join(f"  • {i.product_name} × {i.quantity}" for i in cart_items)
                     if cart_items else "\n🛒 Кошик порожній")
        text = (
            f"👤 *Картка користувача*\n\n"
            f"🙍 {name}\n💬 {username}\n🆔 `{tg_id}`\n"
            f"📱 {user.phone or '—'}\n📧 {user.email or '—'}\n"
            f"🏠 {user.address or '—'}\n"
            f"✅ Виконано замовлень: {done_orders}\n"
            f"📅 З нами: {(user.created_at or '')[:10]}"
            f"{cart_text}"
        )
        try:
            photos = bot.get_user_profile_photos(tg_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                bot.send_photo(call.message.chat.id, file_id, caption=text, parse_mode="Markdown")
                return
        except Exception:
            pass
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

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

    def _show_orders(chat_id, active_only):
        orders = db.get_all_orders(active_only=active_only)
        title = "🔔 Активні замовлення" if active_only else "📋 Всі замовлення"
        if not orders:
            bot.send_message(chat_id, f"{title}\n\n😔 Замовлень немає",
                             reply_markup=kb.admin_panel()); return
        bot.send_message(chat_id, f"{title} — *{len(orders)}* шт.", parse_mode="Markdown")
        for order in orders[:15]:
            _send_admin_order_card(bot, chat_id, order)

    def _send_admin_order_card(bot1, chat_id, order):
        try:
            status_label = ORDER_STATUS_LABELS.get(OrderStatus(order.status), order.status)
        except ValueError:
            status_label = order.status
        name = f"{order.first_name or ''} {order.last_name or ''}".strip() or "—"
        username = f"@{order.username}" if order.username else "—"
        lines = [f"• {i.product_name} × {i.quantity} — {i.price * i.quantity:.2f} грн" for i in order.items]
        ttn_text = f"\n📬 ТТН: `{order.ttn}`" if order.ttn else ""
        text = (
            f"🔖 *Замовлення #{order.id}*\n"
            f"📅 {(order.created_at or '')[:16]}\n"
            f"📊 {status_label}{ttn_text}\n\n"
            f"👤 {name} ({username})\n🆔 `{order.tg_id}`\n📱 {order.phone}\n"
            + (f"🏠 {order.address}\n" if order.address else "")
            + "\n📦 " + "\n".join(lines)
            + f"\n\n💰 *{order.total:.2f} грн*"
        )
        bot1.send_message(chat_id, text, parse_mode="Markdown",
                          reply_markup=kb.admin_order_card(order.id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ord_change_"))
    def adm_ord_change_status(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        order_id = int(call.data.split("_")[3])
        order = db.get_order(order_id)
        if not order: return
        bot.send_message(call.message.chat.id,
            f"🔄 Замовлення *#{order_id}* — оберіть статус:",
            parse_mode="Markdown",
            reply_markup=kb.admin_order_statuses(order_id, order.status))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ord_status_"))
    def adm_ord_set_status(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        parts = call.data.split("_")
        order_id = int(parts[3])
        new_status = "_".join(parts[4:])
        db.update_order_status(order_id, new_status)

        try:
            status_label = ORDER_STATUS_LABELS[OrderStatus(new_status)]
        except Exception:
            status_label = new_status

        # Якщо статус "Відправлено" — запитуємо ТТН
        if new_status == OrderStatus.SHIPPED.value:
            bot.set_state(call.from_user.id, AdminTTNState.waiting_ttn, call.message.chat.id)
            with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
                data["ttn_order_id"] = order_id
                data["ttn_status_label"] = status_label
            bot.send_message(
                call.message.chat.id,
                f"✅ Статус *#{order_id}* → {status_label}\n\n"
                "📬 Введи номер ТТН Нової Пошти\n(/skip — пропустити):",
                parse_mode="Markdown",
                reply_markup=kb.cancel()
            )
            return

        _notify_after_status(bot, call.message.chat.id, order_id, status_label, ttn=None)

    @bot.message_handler(state=AdminTTNState.waiting_ttn, content_types=["text"])
    def adm_save_ttn(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            order_id = data.get("ttn_order_id")
            status_label = data.get("ttn_status_label", "🚚 Відправлено")
        bot.delete_state(message.from_user.id, message.chat.id)

        ttn = None
        if message.text.strip() != "/skip":
            ttn = message.text.strip()
            db.update_order_ttn(order_id, ttn)

        _notify_after_status(bot, message.chat.id, order_id, status_label, ttn=ttn)

    def _notify_after_status(bot1, chat_id, order_id, status_label, ttn):
        bot1.send_message(chat_id,
            f"✅ Статус замовлення *#{order_id}* оновлено:\n{status_label}",
            parse_mode="Markdown", reply_markup=kb.admin_panel())

        order = db.get_order(order_id)
        if not order: return
        ttn_text = f"\n\n📬 Номер накладної: `{ttn}`\nВідстежити: nova.poshta.ua" if ttn else ""
        try:
            bot1.send_message(
                order.tg_id,
                f"🔔 *Статус замовлення #{order_id} оновлено!*\n\n"
                f"📊 {status_label}{ttn_text}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
    def adm_stats(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        s = db.get_stats()
        top_rev = (f"*{s['top_revenue_product'][0]}* — {s['top_revenue_product'][1]:.2f} грн"
                   if s['top_revenue_product'] else "—")
        top_qty = (f"*{s['top_qty_product'][0]}* — {s['top_qty_product'][1]} шт."
                   if s['top_qty_product'] else "—")
        text = (
            "📊 *Статистика магазину*\n\n"
            "💰 *Заробіток*\n"
            f"├ За місяць: *{s['revenue_month']:.2f} грн*\n"
            f"└ За весь час: *{s['revenue_all']:.2f} грн*\n\n"
            "📦 *Замовлення*\n"
            f"├ За місяць: *{s['orders_month']}*\n"
            f"└ За весь час: *{s['orders_all']}*\n\n"
            "🏆 *Топ товари*\n"
            f"├ За виручкою: {top_rev}\n"
            f"└ За кількістю: {top_qty}"
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown",
                         reply_markup=kb.admin_panel())

    @bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast")
    def adm_broadcast(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        users = db.get_all_users()
        bot.set_state(call.from_user.id, BroadcastState.waiting_text, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            f"📢 Розсилка\n\nОтримувачів: {len(users)} користувачів\n\n"
            "Надішли текст повідомлення (можна з фото).\n"
            "Фото надсилай з підписом - він стане текстом розсилки.",
            reply_markup=kb.cancel()
        )

    @bot.message_handler(state=BroadcastState.waiting_text, content_types=["text", "photo"])
    def adm_broadcast_text(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if message.content_type == "photo":
                data["bc_photo_id"] = message.photo[-1].file_id
                data["bc_text"] = message.caption or ""
            else:
                data["bc_photo_id"] = None
                data["bc_text"] = message.text.strip()

        text = data["bc_text"]
        photo_id = data.get("bc_photo_id")
        users = db.get_all_users()

        preview = f"📢 Попередній перегляд:\n\n{text}" if text else "📢 Попередній перегляд: (тільки фото)"
        if photo_id:
            bot.send_photo(message.chat.id, photo_id, caption=preview,
                           reply_markup=kb.admin_broadcast_confirm())
        else:
            bot.send_message(message.chat.id, preview,
                             reply_markup=kb.admin_broadcast_confirm())

        bot.set_state(message.from_user.id, BroadcastState.confirm, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast_confirm")
    def adm_broadcast_send(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            text = data.get("bc_text", "")
            photo_id = data.get("bc_photo_id")
        bot.delete_state(call.from_user.id, call.message.chat.id)

        users = db.get_all_users()
        sent, failed = 0, 0
        for user in users:
            try:
                if photo_id:
                    bot.send_photo(user.tg_id, photo_id, caption=text or None)
                else:
                    bot.send_message(user.tg_id, text)
                sent += 1
            except Exception:
                failed += 1

        bot.send_message(
            call.message.chat.id,
            f"✅ *Розсилку завершено!*\n\n"
            f"📨 Надіслано: {sent}\n"
            f"❌ Не доставлено: {failed}",
            parse_mode="Markdown",
            reply_markup=kb.admin_panel()
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast_cancel")
    def adm_broadcast_cancel(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, "❌ Розсилку скасовано",
                         reply_markup=kb.admin_panel())

    @bot.callback_query_handler(func=lambda c: c.data == "adm_products")
    def adm_products(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
            "📦 *Управління товарами*\n\n"
            "/addproduct — додати\n/editproduct — редагувати\n/removeproduct — видалити",
            parse_mode="Markdown", reply_markup=kb.admin_panel())

    @bot.message_handler(commands=["addproduct"])
    def addproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу"); return
        categories = db.get_categories()
        if not categories:
            db.add_category("Корм", "animals"); db.add_category("Аксесуари", "animals")
            db.add_category("Добрива", "plants"); db.add_category("Ґрунти", "plants")
            categories = db.get_categories()
        bot.set_state(message.from_user.id, AddProductStates.category, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data.clear()
        bot.send_message(message.chat.id, "📦 *Додавання товару*\n\nОберіть категорію:",
                         reply_markup=kb.add_product_categories(categories), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data == "addproduct_cancel")
    def addproduct_cancel_cb(call):
        bot.answer_callback_query(call.id)
        bot.delete_state(call.from_user.id, call.message.chat.id)
        bot.send_message(call.message.chat.id, "❌ Скасовано", reply_markup=kb.main_menu())

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
            bot.send_message(message.chat.id, "⚠️ Занадто коротко"); return
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
            bot.send_message(message.chat.id, "⚠️ Невірна ціна"); return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["price"] = price
        bot.set_state(message.from_user.id, AddProductStates.stock, message.chat.id)
        bot.send_message(message.chat.id, "📦 Введи кількість:", reply_markup=kb.cancel())

    @bot.message_handler(state=AddProductStates.stock, content_types=["text"])
    def addproduct_stock(message):
        if not message.text.strip().isdigit() or int(message.text.strip()) < 0:
            bot.send_message(message.chat.id, "⚠️ Введи ціле число >= 0"); return
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
            bot.send_message(message.chat.id, "⚠️ Надішли фото або /skip"); return
        _save_product(bot, message, None)

    def _save_product(bot1, message, photo_id):
        with bot1.retrieve_data(message.from_user.id, message.chat.id) as data:
            product = db.add_product(
                category_id=data["category_id"], name=data["name"],
                description=data.get("description"), price=data["price"],
                stock=data["stock"], photo_id=photo_id,
            )
        bot1.delete_state(message.from_user.id, message.chat.id)
        bot1.send_message(message.chat.id,
            f"✅ *Товар додано!*\n\n📦 {product.name}\n💰 {product.price} грн\n🗂 {product.stock} шт.",
            parse_mode="Markdown", reply_markup=kb.main_menu())

    @bot.message_handler(commands=["editproduct"])
    def editproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу"); return
        products = db.get_all_products()
        if not products:
            bot.send_message(message.chat.id, "😔 Товарів ще немає"); return
        bot.send_message(message.chat.id, "✏️ *Редагування*\n\nОберіть товар:",
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
        if not product: return
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
            "name": "📝 Нова назва:",
            "desc": "📄 Новий опис (/skip — очистити):",
            "price": "💰 Нова ціна:",
            "stock": "📦 Нова кількість:",
            "photo": "🖼 Нове фото (/skip — без фото):",
        }
        bot.set_state(call.from_user.id, EditProductStates.enter_value, call.message.chat.id)
        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["edit_product_id"] = product_id
            data["edit_field_key"] = field_key
        bot.send_message(call.message.chat.id, prompts.get(field_key, "Введи значення:"),
                         reply_markup=kb.cancel())

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
            result = "Опис очищено" if val is None else "Опис оновлено"
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

    @bot.message_handler(commands=["removeproduct"])
    def removeproduct_start(message):
        if not is_admin(message):
            bot.send_message(message.chat.id, "⛔️ Немає доступу"); return
        products = db.get_all_products()
        if not products:
            bot.send_message(message.chat.id, "😔 Товарів ще немає"); return
        bot.send_message(message.chat.id, "🗑 *Видалення*\n\nОберіть товар:",
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
        if not product: return
        bot.send_message(call.message.chat.id,
            f"⚠️ Видалити *{product.name}*?\n💰 {product.price} грн | 📦 {product.stock} шт.",
            parse_mode="Markdown", reply_markup=kb.confirm_remove(product_id))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rm_confirm_"))
    def removeproduct_do(call):
        if not is_admin_call(call): return
        bot.answer_callback_query(call.id)
        product_id = int(call.data.split("_")[2])
        product = db.get_product_by_id(product_id)
        name = product.name if product else "Товар"
        db.delete_product(product_id)
        bot.send_message(call.message.chat.id, f"✅ *{name}* видалено!",
                         parse_mode="Markdown", reply_markup=kb.main_menu())
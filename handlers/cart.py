import db
import keyboards as kb
import ua

def register(bot):

    @bot.message_handler(commands=["cart"])
    @bot.message_handler(func=lambda m: m.text == "🛒 Корзина")
    def show_cart(message):
        _send_cart(bot, message.chat.id, message.from_user.id)

    def _send_cart(bot1, chat_id: int, tg_id: int):
        items = db.cart_get(tg_id)
        if not items:
            bot1.send_message(
                chat_id,
                "🛒 Ваш кошик порожній\n\nДодайте товари через каталог 👇",
                reply_markup=kb.cart_view([])
            )
            return
        total = sum(i.product_price * i.quantity for i in items)
        lines = [f"• {i.product_name} × {i.quantity} = {i.product_price * i.quantity:.2f} грн" for i in items]
        text = (
            "🛒 *Ваш кошик*\n\n"
            + "\n".join(lines)
            + f"\n\n💰 *Разом: {total:.2f} грн*\n\n"
            "Натисніть ❌ поруч із товаром, щоб видалити його"
        )
        bot1.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb.cart_view(items))

    @bot.callback_query_handler(func=lambda c: c.data.startswith("cart_del_"))
    def cart_del(call):
        product_id = int(call.data.split("_")[2])
        db.cart_remove(call.from_user.id, product_id)
        bot.answer_callback_query(call.id, "🗑 Видалено")
        items = db.cart_get(call.from_user.id)
        if not items:
            try:
                bot.edit_message_text(
                    "🛒 Кошик порожній",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=kb.cart_view([])
                )
            except Exception:
                pass
            return
        total = sum(i.product_price * i.quantity for i in items)
        lines = [f"• {i.product_name} × {i.quantity} = {i.product_price * i.quantity:.2f} грн" for i in items]
        text = (
            "🛒 *Ваш кошик*\n\n"
            + "\n".join(lines)
            + f"\n\n💰 *Разом: {total:.2f} грн*\n\n"
            "Натисніть ❌ поруч із товаром, щоб видалити його"
        )
        try:
            bot.edit_message_text(
                text, call.message.chat.id, call.message.message_id,
                parse_mode="Markdown", reply_markup=kb.cart_view(items)
            )
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda c: c.data == "cart_clear")
    def cart_clear(call):
        db.cart_clear(call.from_user.id)
        bot.answer_callback_query(call.id, "🗑 Кошик очищено")
        try:
            bot.edit_message_text(
                "🛒 Кошик порожній",
                call.message.chat.id, call.message.message_id,
                reply_markup=kb.cart_view([])
            )
        except Exception:
            pass

    # ── Checkout ───────────────────────────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data == "cart_checkout")
    def cart_checkout(call):
        bot.answer_callback_query(call.id)
        items = db.cart_get(call.from_user.id)
        if not items:
            bot.answer_callback_query(call.id, "Кошик порожній", show_alert=True)
            return

        user = db.get_user(call.from_user.id)
        if not user or not user.phone:
            # Просимо поділитися номером через Telegram
            bot.send_message(
                call.message.chat.id,
                "📱 Для оформлення замовлення потрібен ваш номер телефону.\n\n"
                "Натисніть кнопку нижче, щоб поділитися номером:",
                reply_markup=kb.request_phone()
            )
            # Зберігаємо стан «чекаємо телефон для checkout»
            bot.set_state(call.from_user.id, "checkout_wait_phone", call.message.chat.id)
            return

        _finish_checkout(bot, call.message.chat.id, call.from_user.id, user.phone)

    @bot.message_handler(state="checkout_wait_phone", content_types=["contact"])
    def checkout_contact(message):
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
        db.update_user_field(message.from_user.id, "phone", phone)
        bot.delete_state(message.from_user.id, message.chat.id)
        _finish_checkout(bot, message.chat.id, message.from_user.id, phone)

    @bot.message_handler(state="checkout_wait_phone", content_types=["text"])
    def checkout_phone_cancel(message):
        if message.text == "🔙 Скасувати":
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(message.chat.id, "❌ Оформлення скасовано", reply_markup=kb.main_menu())

    def _finish_checkout(bot1, chat_id: int, tg_id: int, phone: str):
        items = db.cart_get(tg_id)
        if not items:
            bot1.send_message(chat_id, "🛒 Кошик порожній", reply_markup=kb.main_menu())
            return
        user = db.get_user(tg_id)
        order = db.create_order(
            tg_id=tg_id,
            phone=phone,
            address=user.address if user else None,
            comment=None,
            items=items
        )
        db.cart_clear(tg_id)

        lines = [f"• {i.product_name} × {i.quantity} — {i.price * i.quantity:.2f} грн" for i in order.items]
        text = (
            "✅ *Замовлення оформлено!*\n\n"
            f"🔖 Номер замовлення: *#{order.id}*\n"
            f"📱 Телефон: {phone}\n"
            + (f"🏠 Адреса: {user.address}\n" if user and user.address else "")
            + f"\n📦 Товари:\n" + "\n".join(lines)
            + f"\n\n💰 *Разом: {order.total:.2f} грн*\n\n"
            "З вами зв'яжеться наш менеджер 🙂"
        )
        bot1.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb.main_menu())
import db
import keyboards as kb
from models import ORDER_STATUS_LABELS, OrderStatus, CANCELLABLE_BY_USER

def register(bot):

    @bot.message_handler(commands=["orders"])
    @bot.message_handler(func=lambda m: m.text == "📦 Мої замовлення")
    def my_orders(message):
        orders = db.get_orders_by_user(message.from_user.id)
        if not orders:
            bot.send_message(message.chat.id, "📦 У вас ще немає замовлень", reply_markup=kb.main_menu())
            return
        bot.send_message(message.chat.id, f"📦 *Ваші замовлення* — {len(orders)} шт.",
                         parse_mode="Markdown")
        for order in orders[:10]:
            _send_order_card(bot, message.chat.id, order)

    def _send_order_card(bot1, chat_id: int, order):
        try:
            status_obj = OrderStatus(order.status)
            status_label = ORDER_STATUS_LABELS.get(status_obj, order.status)
            can_cancel = status_obj in CANCELLABLE_BY_USER
        except ValueError:
            status_label = order.status
            can_cancel = False

        lines = [f"• {i.product_name} × {i.quantity} — {i.price * i.quantity:.2f} грн"
                 for i in order.items]
        created = order.created_at[:16] if order.created_at else "—"

        ttn_text = f"\n📬 ТТН: `{order.ttn}`" if order.ttn else ""

        text = (
            f"🔖 *Замовлення #{order.id}*\n"
            f"📅 {created}\n"
            f"📊 Статус: {status_label}"
            f"{ttn_text}\n\n"
            + "\n".join(lines)
            + f"\n\n💰 *Разом: {order.total:.2f} грн*"
        )
        bot1.send_message(chat_id, text, parse_mode="Markdown",
                          reply_markup=kb.order_card_user(order.id, can_cancel=can_cancel))

    # ── Скасування замовлення клієнтом ────────────────────────────────────────

    @bot.callback_query_handler(func=lambda c: c.data.startswith("user_cancel_order_"))
    def user_cancel_ask(call):
        bot.answer_callback_query(call.id)
        order_id = int(call.data.split("_")[3])
        order = db.get_order(order_id)
        if not order or order.tg_id != call.from_user.id:
            return
        bot.send_message(
            call.message.chat.id,
            f"⚠️ Ви впевнені, що хочете скасувати *замовлення #{order_id}*?\n\n"
            "Товари буде повернуто на склад.",
            parse_mode="Markdown",
            reply_markup=kb.confirm_cancel_order(order_id)
        )

    @bot.callback_query_handler(func=lambda c: c.data.startswith("user_cancel_confirm_"))
    def user_cancel_confirm(call):
        bot.answer_callback_query(call.id)
        order_id = int(call.data.split("_")[3])
        order = db.get_order(order_id)
        if not order or order.tg_id != call.from_user.id:
            return
        try:
            status_obj = OrderStatus(order.status)
            if status_obj not in CANCELLABLE_BY_USER:
                bot.send_message(call.message.chat.id,
                    "⚠️ Це замовлення вже не можна скасувати — воно в обробці.\n"
                    "Зверніться до менеджера.", reply_markup=kb.main_menu())
                return
        except ValueError:
            pass

        db.update_order_status(order_id, OrderStatus.CANCELLED.value)
        db.restore_stock_for_order(order_id)
        bot.send_message(call.message.chat.id,
            f"✅ Замовлення *#{order_id}* скасовано.\nТовари повернуто на склад.",
            parse_mode="Markdown", reply_markup=kb.main_menu())

    @bot.callback_query_handler(func=lambda c: c.data.startswith("user_cancel_no_"))
    def user_cancel_no(call):
        bot.answer_callback_query(call.id, "Скасування відмінено")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
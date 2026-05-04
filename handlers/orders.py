import db
import keyboards as kb
from models import ORDER_STATUS_LABELS, OrderStatus

def register(bot):

    @bot.message_handler(commands=["orders"])
    @bot.message_handler(func=lambda m: m.text == "📦 Мої замовлення")
    def my_orders(message):
        orders = db.get_orders_by_user(message.from_user.id)
        if not orders:
            bot.send_message(message.chat.id, "📦 У вас ще немає замовлень", reply_markup=kb.main_menu())
            return

        bot.send_message(message.chat.id, f"📦 *Ваші замовлення* — {len(orders)} шт.", parse_mode="Markdown")
        for order in orders[:10]:  # показуємо останні 10
            _send_order_card(bot, message.chat.id, order)

    def _send_order_card(bot1, chat_id: int, order):
        try:
            status_obj = OrderStatus(order.status)
            status_label = ORDER_STATUS_LABELS.get(status_obj, order.status)
        except ValueError:
            status_label = order.status

        lines = [f"• {i.product_name} × {i.quantity} — {i.price * i.quantity:.2f} грн" for i in order.items]
        created = order.created_at[:16] if order.created_at else "—"
        text = (
            f"🔖 *Замовлення #{order.id}*\n"
            f"📅 {created}\n"
            f"📊 Статус: {status_label}\n\n"
            + "\n".join(lines)
            + f"\n\n💰 *Разом: {order.total:.2f} грн*"
        )
        bot1.send_message(chat_id, text, parse_mode="Markdown")
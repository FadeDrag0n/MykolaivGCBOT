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
        lines = []
        for i in items:
            lines.append(f"• {i.product_name} × {i.quantity} = {i.product_price * i.quantity:.2f} грн")
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
        # Refresh cart message
        items = db.cart_get(call.from_user.id)
        if not items:
            bot.edit_message_text(
                "🛒 Кошик порожній",
                call.message.chat.id,
                call.message.message_id,
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
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=kb.cart_view(items)
        )

    @bot.callback_query_handler(func=lambda c: c.data == "cart_clear")
    def cart_clear(call):
        db.cart_clear(call.from_user.id)
        bot.answer_callback_query(call.id, "🗑 Кошик очищено")
        bot.edit_message_text(
            "🛒 Кошик порожній",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb.cart_view([])
        )

    @bot.callback_query_handler(func=lambda c: c.data == "cart_checkout")
    def cart_checkout(call):
        bot.answer_callback_query(call.id)
        items = db.cart_get(call.from_user.id)
        if not items:
            bot.answer_callback_query(call.id, "Кошик порожній", show_alert=True)
            return
        # Placeholder — оформлення замовлення буде реалізоване окремо
        bot.send_message(
            call.message.chat.id,
            "✅ Дякуємо за замовлення!\n\n"
            "Незабаром з вами зв'яжеться менеджер для підтвердження.\n\n"
            "_(Функціонал оформлення в розробці)_",
            parse_mode="Markdown",
            reply_markup=kb.main_menu()
        )
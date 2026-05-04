import db
import keyboards as kb

def register(bot, admin_id):

    @bot.message_handler(commands=["stats"])
    def stats_handler(message):
        if message.from_user.id != admin_id:
            bot.send_message(message.chat.id, "⛔️ Немає доступу")
            return
        _send_stats(bot, message.chat.id)

    def _send_stats(bot1, chat_id: int):
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
        bot1.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb.main_menu())
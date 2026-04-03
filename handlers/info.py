import ua
import keyboards as kb
import db
from telebot.handler_backends import State, StatesGroup

class InfoStates(StatesGroup):
    waiting_phone   = State()
    waiting_email   = State()
    waiting_address = State()

def register(bot):

    # --- показати інфо ---
    @bot.message_handler(commands=["info"])
    @bot.message_handler(func=lambda m: m.text == "👤 Контактна інформація")
    def info_handler(message):
        user = db.get_user(message.from_user.id)
        bot.send_message(
            message.chat.id,
            ua.info_message(user),
            reply_markup=kb.info(),
            parse_mode="Markdown",
        )

    # --- натиснули кнопку редагування ---
    @bot.callback_query_handler(func=lambda c: c.data == "info_phone")
    def ask_phone(call):
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, InfoStates.waiting_phone, call.message.chat.id)
        bot.send_message(call.message.chat.id, "📱 Введи номер телефону:\nНаприклад: +380991234567")

    @bot.callback_query_handler(func=lambda c: c.data == "info_email")
    def ask_email(call):
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, InfoStates.waiting_email, call.message.chat.id)
        bot.send_message(call.message.chat.id, "📧 Введи email:\nНаприклад: example@gmail.com")

    @bot.callback_query_handler(func=lambda c: c.data == "info_address")
    def ask_address(call):
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, InfoStates.waiting_address, call.message.chat.id)
        bot.send_message(call.message.chat.id, "🏠 Введи адресу доставки:\nНаприклад: м. Київ, вул. Хрещатик 1, кв. 5")

    # --- отримали відповідь ---
    @bot.message_handler(state=InfoStates.waiting_phone)
    def save_phone(message):
        phone = message.text.strip()
        if not phone.startswith("+") or not phone[1:].isdigit() or len(phone) < 10:
            bot.send_message(message.chat.id, "⚠️ Невірний формат. Введи номер у форматі +380991234567")
            return
        db.update_user_field(message.from_user.id, "phone", phone)
        bot.delete_state(message.from_user.id, message.chat.id)
        user = db.get_user(message.from_user.id)
        bot.send_message(message.chat.id, "✅ Номер збережено!", reply_markup=kb.info())
        bot.send_message(message.chat.id, ua.info_message(user), reply_markup=kb.info(), parse_mode="Markdown")

    @bot.message_handler(state=InfoStates.waiting_email)
    def save_email(message):
        email = message.text.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            bot.send_message(message.chat.id, "⚠️ Невірний формат. Введи email як example@gmail.com")
            return
        db.update_user_field(message.from_user.id, "email", email)
        bot.delete_state(message.from_user.id, message.chat.id)
        user = db.get_user(message.from_user.id)
        bot.send_message(message.chat.id, "✅ Email збережено!")
        bot.send_message(message.chat.id, ua.info_message(user), reply_markup=kb.info(), parse_mode="Markdown")

    @bot.message_handler(state=InfoStates.waiting_address)
    def save_address(message):
        address = message.text.strip()
        if len(address) < 5:
            bot.send_message(message.chat.id, "⚠️ Адреса занадто коротка, введи повну адресу")
            return
        db.update_user_field(message.from_user.id, "address", address)
        bot.delete_state(message.from_user.id, message.chat.id)
        user = db.get_user(message.from_user.id)
        bot.send_message(message.chat.id, "✅ Адресу збережено!")
        bot.send_message(message.chat.id, ua.info_message(user), reply_markup=kb.info(), parse_mode="Markdown")
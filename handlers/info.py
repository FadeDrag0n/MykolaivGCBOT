import ua
import keyboards as kb
import db
from telebot.handler_backends import State, StatesGroup

class InfoStates(StatesGroup):
    waiting_phone   = State()
    waiting_email   = State()
    waiting_address = State()

def register(bot):

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

    @bot.callback_query_handler(func=lambda c: c.data == "info_phone")
    def ask_phone(call):
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, InfoStates.waiting_phone, call.message.chat.id)
        bot.send_message(
            call.message.chat.id,
            "📱 Поділіться номером телефону через кнопку нижче:",
            reply_markup=kb.request_phone()
        )

    @bot.callback_query_handler(func=lambda c: c.data == "info_email")
    def ask_email(call):
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, InfoStates.waiting_email, call.message.chat.id)
        bot.send_message(call.message.chat.id, "📧 Введи email:\nНаприклад: example@gmail.com", reply_markup=kb.cancel())

    @bot.callback_query_handler(func=lambda c: c.data == "info_address")
    def ask_address(call):
        bot.answer_callback_query(call.id)
        bot.set_state(call.from_user.id, InfoStates.waiting_address, call.message.chat.id)
        bot.send_message(call.message.chat.id, "🏠 Введи адресу доставки:\nНаприклад: м. Київ, вул. Хрещатик 1, кв. 5", reply_markup=kb.cancel())

    # ── Phone via contact ──────────────────────────────────────────────────────

    @bot.message_handler(state=InfoStates.waiting_phone, content_types=["contact"])
    def save_phone_contact(message):
        phone = message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
        db.update_user_field(message.from_user.id, "phone", phone)
        bot.delete_state(message.from_user.id, message.chat.id)
        user = db.get_user(message.from_user.id)
        bot.send_message(message.chat.id, "✅ Номер збережено!", reply_markup=kb.main_menu())
        bot.send_message(message.chat.id, ua.info_message(user), reply_markup=kb.info(), parse_mode="Markdown")

    @bot.message_handler(state=InfoStates.waiting_phone, content_types=["text"])
    def phone_cancel(message):
        if message.text == "🔙 Скасувати":
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(message.chat.id, "❌ Скасовано", reply_markup=kb.main_menu())
        else:
            bot.send_message(message.chat.id, "⚠️ Будь ласка, скористайтесь кнопкою «📱 Поділитися номером»")

    # ── Email ──────────────────────────────────────────────────────────────────

    @bot.message_handler(state=InfoStates.waiting_email, content_types=["text"])
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

    # ── Address ────────────────────────────────────────────────────────────────

    @bot.message_handler(state=InfoStates.waiting_address, content_types=["text"])
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
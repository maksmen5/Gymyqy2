import telebot
from telebot import types
from flask import Flask, request
from config import BOT_TOKEN, COURSES, CHANNELS

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

ADMIN_CHAT_ID = 1384804489
user_state = {}

# --- Меню ---
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(course['name']) for course in COURSES.values()]
    markup.add(*buttons)
    bot.send_message(chat_id, "👋 Обери курс:", reply_markup=markup)

def show_course_menu(chat_id, course_id):
    course = COURSES[course_id]
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("ℹ️ Інформація"),
        types.KeyboardButton("💳 Купити"),
        types.KeyboardButton("⬅️ Назад")
    )
    bot.send_message(chat_id, f"📘 {course['name']}", reply_markup=markup)

# --- Основна логіка ---
@bot.message_handler(commands=['start'])
def start(message):
    user_state.pop(message.chat.id, None)
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    for cid, course in COURSES.items():
        if text == course['name']:
            user_state[chat_id] = cid
            show_course_menu(chat_id, cid)
            return

    if chat_id in user_state:
        cid = user_state[chat_id]
        course = COURSES[cid]

        if text == "ℹ️ Інформація":
            bot.send_message(chat_id, f"*{course['name']}*\n\n{course['description']}", parse_mode="Markdown")

        elif text == "💳 Купити":
            if course['price'] == 0:
                handle_successful_payment(chat_id, cid)
                return

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Я оплатив", callback_data=f"confirm_payment:{cid}"))

bot.send_message(
    chat_id,
    f"""💳 Сплати *{course['price']} грн* на карту: `4441 1144 2233 4455`

Після оплати натисни кнопку нижче.""",
    parse_mode="Markdown",
    reply_markup=markup
)



        elif text == "⬅️ Назад":
            user_state.pop(chat_id, None)
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "❗️ Оберіть кнопку з меню.")
    else:
        bot.send_message(chat_id, "❗️ Оберіть курс з меню.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_payment"))
def confirm_payment_callback(call):
    cid = call.data.split(":")[1]
    user = call.from_user
    chat_id = call.message.chat.id

    bot.send_message(
        ADMIN_CHAT_ID,
        f"📝 Заявка на оплату\n"
        f"Користувач: @{user.username or 'немає'}\n"
        f"ID: {user.id}\n"
        f"Курс: {COURSES[cid]['name']}\n"
        f"Сума: {COURSES[cid]['price']}\n"
        f"Підтвердити: /confirm_{user.id}_{cid}"
    )

    bot.answer_callback_query(call.id, "Заявка надіслана. Очікуй підтвердження.")
    bot.send_message(chat_id, "🔄 Очікуємо підтвердження оплати від адміна")

@bot.message_handler(func=lambda message: message.text.startswith("/confirm_"))
def confirm_payment_command(message):
    parts = message.text.split("_")
    if len(parts) != 3:
        bot.reply_to(message, "❌ Невірний формат. Приклад: /confirm_USERID_COURSEID")
        return
    user_id, course_id = parts[1], parts[2]
    handle_successful_payment(int(user_id), course_id)
    bot.reply_to(message, "✅ Доступ видано.")

@bot.message_handler(func=lambda message: message.text.startswith("/revoke_"))
def revoke_access(message):
    parts = message.text.split("_")
    if len(parts) != 3:
        bot.reply_to(message, "❌ Невірний формат. Приклад: /revoke_USERID_COURSEID")
        return
    user_id, course_id = parts[1], parts[2]
    try:
        bot.ban_chat_member(chat_id=CHANNELS[course_id], user_id=int(user_id))
        bot.unban_chat_member(chat_id=CHANNELS[course_id], user_id=int(user_id))
        bot.reply_to(message, f"🚫 Доступ до курсу {course_id} для користувача {user_id} скасовано.")
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {e}")

def handle_successful_payment(user_id, course_id):
    try:
        chat_id = CHANNELS.get(course_id)
        if not chat_id:
            bot.send_message(user_id, "❌ Канал не знайдено.")
            return
        invite = bot.create_chat_invite_link(
            chat_id=chat_id,
            member_limit=1,
            creates_join_request=False
        )
        bot.send_message(user_id, f"✅ Доступ підтверджено!\n🔗 Посилання:\n{invite.invite_link}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Помилка доступу:\n{e}")
        print(f"[ERROR] handle_successful_payment: {e}")

# --- Webhook ---
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Invalid content-type', 403

if __name__ == '__main__':
    import os
    bot.remove_webhook()
    WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/"
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=5000)

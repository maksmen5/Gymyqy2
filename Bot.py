import telebot
from flask import Flask, request
from config import BOT_TOKEN, COURSES, CHANNELS, ADMIN_CHAT_ID, WEBHOOK_URL

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Словник для збереження вибору користувача
user_course_choice = {}

# Команда /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for key, course in COURSES.items():
        markup.add(telebot.types.InlineKeyboardButton(course["name"], callback_data=f"course_{key}"))
    bot.send_message(message.chat.id, "👋 Привіт! Обери курс:", reply_markup=markup)

# Обробка вибору курсу
@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def handle_course_selection(call):
    course_key = call.data.split("_")[1]
    course = COURSES[course_key]
    user_course_choice[call.from_user.id] = course_key

    if course["price"] == 0:
        try:
            invite_link = bot.create_chat_invite_link(CHANNELS[course_key], member_limit=1).invite_link
            bot.send_message(call.message.chat.id, f"✅ Ось доступ до курсу *{course['name']}*:\n{invite_link}", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Не вдалося створити інвайт: {e}")
    else:
        bot.send_message(
            call.message.chat.id,
            f"""💳 Сплати *{course['price']} грн* на картку: `4441 1144 2233 4455`

📩 Після оплати, напиши /confirm і надай підтвердження адміну.

Після оплати натисни кнопку нижче.""",
            parse_mode="Markdown"
        )

# Обробка /confirm
@bot.message_handler(commands=["confirm"])
def handle_confirm(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    course_key = user_course_choice.get(user_id)

    if not course_key:
        bot.send_message(message.chat.id, "❌ Спочатку обери курс.")
        return

    course = COURSES[course_key]
    text = f"""🔔 Користувач @{username} хоче доступ до курсу *{course['name']}*.

✅ Підтвердити: /confirm_{user_id}_{course_key}
❌ Відкликати: /revoke_{user_id}
"""
    bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
    bot.send_message(message.chat.id, "⏳ Очікуй підтвердження від адміністратора.")

# Підтвердження доступу (адмін)
@bot.message_handler(commands=['confirm_'])
def admin_confirm_access(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    try:
        _, user_id, course_key = message.text.split("_")
        user_id = int(user_id)
        invite_link = bot.create_chat_invite_link(CHANNELS[course_key], member_limit=1).invite_link
        bot.send_message(user_id, f"✅ Доступ до курсу *{COURSES[course_key]['name']}*:\n{invite_link}", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {e}")

# Відкликання доступу (адмін)
@bot.message_handler(commands=['revoke_'])
def admin_revoke(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return

    try:
        _, user_id = message.text.split("_")
        user_id = int(user_id)
        bot.send_message(user_id, "❌ Доступ не підтверджено. Якщо це помилка — звернись до адміністратора.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {e}")

# Webhook endpoint
@app.route('/', methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    else:
        return "Invalid", 403

# Встановлення webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# Запуск Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

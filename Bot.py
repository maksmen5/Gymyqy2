import telebot
from telebot import types
from flask import Flask, request
import config

TOKEN = config.BOT_TOKEN
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

ADMIN_CHAT_ID = 1384804489  # 🔐 Замінити на твій Telegram ID
confirmed_users = {}
payments = {}

# 🌐 Webhook URL (Render буде підставляти свій)
WEBHOOK_URL = "https://your-render-url.onrender.com/"  # Заміни на свій реальний URL


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, course in config.COURSES.items():
        markup.add(types.KeyboardButton(course['name']))
    bot.send_message(message.chat.id, "👋 Привіт! Обери курс нижче:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in [c['name'] for c in config.COURSES.values()])
def handle_course_selection(message):
    user_id = message.chat.id
    course_key = next(k for k, v in config.COURSES.items() if v['name'] == message.text)
    course = config.COURSES[course_key]

    if course['price'] == 0:
        invite_link = bot.create_chat_invite_link(chat_id=config.CHANNELS[course_key], member_limit=1).invite_link
        bot.send_message(user_id, f"✅ Ось твій доступ до курсу: {invite_link}")
    else:
        payments[user_id] = course_key
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Я оплатив", callback_data="confirm_payment"))
        bot.send_message(
            user_id,
            f"💳 Сплати *{course['price']} грн* на карту: `4441 1144 2233 4455`

Після оплати натисни кнопку нижче.",
            parse_mode="Markdown",
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def confirm_payment(call):
    user_id = call.from_user.id
    if user_id not in payments:
        bot.send_message(user_id, "❗️ Оберіть курс спочатку через меню.")
        return
    course_key = payments[user_id]
    bot.send_message(ADMIN_CHAT_ID, f"📥 Користувач @{call.from_user.username or call.from_user.id} подав заявку на оплату курсу: {course_key}.")
    bot.send_message(user_id, "📨 Заявку надіслано. Очікуй підтвердження від адміністратора.")


@bot.message_handler(commands=['confirm'])
def admin_confirm(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        course_key = parts[2]
        invite_link = bot.create_chat_invite_link(chat_id=config.CHANNELS[course_key], member_limit=1).invite_link
        bot.send_message(user_id, f"✅ Доступ надано: {invite_link}")
        confirmed_users[user_id] = course_key
    except:
        bot.send_message(ADMIN_CHAT_ID, "⚠️ Формат: /confirm user_id course_key")


@bot.message_handler(commands=['revoke'])
def admin_revoke(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        course_key = parts[2]
        bot.send_message(user_id, "🚫 Ваш доступ було відкликано адміністратором.")
        confirmed_users.pop(user_id, None)
    except:
        bot.send_message(ADMIN_CHAT_ID, "⚠️ Формат: /revoke user_id course_key")


@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'ok', 200


# 🔧 Поставити вебхук при старті
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# ✅ Запуск Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

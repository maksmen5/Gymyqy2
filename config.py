# config.py

import os
from dotenv import load_dotenv
load_dotenv()

# 🔐 Дані бота
WEBHOOK_URL = "https://telebot-zydo.onrender.com"
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# 👮‍♂️ ID адміна для підтвердження оплат
ADMIN_CHAT_ID = 1384804489 

# 📦 Курси
COURSES = {
    "gym": {"name": "Тренування в залі", "price": 400, "description": "Програма тренувань у залі."},
    "bodybuilding": {"name": "Бодібілдинг", "price": 500, "description": "Класичний набір маси."},
    "power": {"name": "Пауерліфтинг", "price": 600, "description": "Жим, присід, тяга для сили."},
    "home": {"name": "Домашні тренування", "price": 0, "description": "Безкоштовна програма вдома."},
    "food": {"name": "План Харчування", "price": 300, "description": "Раціон для росту та сушки."},
    "coach_chat": {"name": "Чат з тренером", "price": 100, "description": "2 дні особистих відповідей."}
}

# 📍 ID або @юзернейми каналів (перевір, що бот є адміністратором кожного!)
CHANNELS = {
    "gym": -1002670190226,
    "bodybuilding": -1002276754295,
    "power": -1002859055550,
    "home": -1002544564658,
    "food": -1002752947894,
    "steroids": -1002717013491,
    "coach_chat": -1007777777777
}  # ← обов'язково закрита дужка!

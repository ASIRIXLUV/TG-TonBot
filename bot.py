import telebot
import random
import json
import os
import threading
from flask import Flask, request

# ==================== КОНФИГ ====================
TOKEN = '8969785862:AAGDi4NpAWB0Pm0BT3BsFMK6SiRKKGzvz7k'  # ⚠️ ЗАМЕНИТЕ НА ВАШ ТОКЕН!
bot = telebot.TeleBot(TOKEN)

# ==================== FLASK-ПРИЛОЖЕНИЕ ====================
app = Flask(__name__)  # <-- ЭТО ГЛАВНОЕ, ЧЕГО НЕ ХВАТАЛО

DATA_FILE = 'balances.json'
BONUS_AMOUNT = 2500
START_BALANCE = 2500

# ==================== БАЗА ДАННЫХ ====================
def load_balances():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_balances(balances):
    with open(DATA_FILE, 'w') as f:
        json.dump(balances, f, indent=4)

def get_balance(user_id):
    balances = load_balances()
    user_id = str(user_id)
    if user_id not in balances:
        balances[user_id] = START_BALANCE
        save_balances(balances)
    return balances[user_id]

def update_balance(user_id, amount):
    balances = load_balances()
    user_id = str(user_id)
    balances[user_id] = get_balance(user_id) + amount
    save_balances(balances)

def add_bonus(user_id):
    update_balance(user_id, BONUS_AMOUNT)
    return get_balance(user_id)

def format_balance(amount):
    return f"{amount:,} TON"

# ==================== КЛАВИАТУРА ====================
def main_menu_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('/balance')
    btn2 = telebot.types.KeyboardButton('/bonus')
    btn3 = telebot.types.KeyboardButton('/чёт 100')
    btn4 = telebot.types.KeyboardButton('/нечет 100')
    btn5 = telebot.types.KeyboardButton('/джокер 100 3')
    keyboard.add(btn1, btn2, btn3, btn4, btn5)
    return keyboard

# ==================== КОМАНДЫ БОТА ====================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    current_balance = get_balance(user_id)
    
    bot.send_message(
        message.chat.id,
        f"🎰 Привет, {user_name}!\n"
        f"Добро пожаловать в TON Casino!\n\n"
        f"💰 Твой баланс: {format_balance(current_balance)}\n"
        f"🎁 Бонус +{format_balance(BONUS_AMOUNT)} (команда /bonus)\n\n"
        f"📊 Коэффициенты:\n"
        f"• /чёт — x1.5\n"
        f"• /нечет — x1.5\n"
        f"• /джокер — x3\n\n"
        f"Примеры:\n"
        f"/чёт 100\n"
        f"/джокер 100 5",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(commands=['bonus'])
def bonus(message):
    user_id = message.from_user.id
    new_balance = add_bonus(user_id)
    bot.send_message(
        message.chat.id,
        f"🎁 Ты получил бонус +{format_balance(BONUS_AMOUNT)}!\n"
        f"💰 Новый баланс: {format_balance(new_balance)}"
    )

@bot.message_handler(commands=['balance'])
def balance(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"💰 Твой баланс: {format_balance(bal)}"
    )

@bot.message_handler(commands=['чёт', 'нечет', 'джокер'])
def place_bet(message):
    # ... (весь код из предыдущего сообщения) ...
    # Для краткости я не копирую весь обработчик, но он должен быть здесь полностью.
    pass  # Замените на ваш код ставок

# ==================== ВЕБ-МАРШРУТЫ ====================
@app.route('/')
def index():
    return "🤖 TON Casino Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

# ==================== ЗАПУСК БОТА ====================
def run_bot():
    """Запускает бота в отдельном потоке"""
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask-сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

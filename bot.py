import telebot
import random
import json
import os
import threading
from flask import Flask, request

# ==================== КОНФИГ ====================
# ⚠️ НЕ ХРАНИ ТОКЕН В КОДЕ! Используй переменные окружения!
TOKEN = os.environ.get('8969785862:AAGDi4NpAWB0Pm0BT3BsFMK6SiRKKGzvz7k')  # Безопасно!
if not TOKEN:
    raise ValueError("❌ Токен не найден! Установи переменную TELEGRAM_BOT_TOKEN в Render.")

bot = telebot.TeleBot(TOKEN)

# ==================== FLASK-ПРИЛОЖЕНИЕ ====================
app = Flask(__name__)

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

# ==================== КЛАВИАТУРА С КНОПКАМИ ====================
def main_menu_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_balance = telebot.types.KeyboardButton('💰 Баланс')
    btn_bonus = telebot.types.KeyboardButton('🎁 Бонус')
    btn_even = telebot.types.KeyboardButton('🎲 Чёт 100')
    btn_odd = telebot.types.KeyboardButton('🎲 Нечет 100')
    btn_joker = telebot.types.KeyboardButton('🃏 Джокер 100 3')
    keyboard.add(btn_balance, btn_bonus)
    keyboard.add(btn_even, btn_odd)
    keyboard.add(btn_joker)
    return keyboard

# ==================== ОБРАБОТЧИКИ КНОПОК ====================
@bot.message_handler(func=lambda message: message.text == '💰 Баланс')
def button_balance(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"💰 Твой баланс: {format_balance(bal)}",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == '🎁 Бонус')
def button_bonus(message):
    user_id = message.from_user.id
    new_balance = add_bonus(user_id)
    bot.send_message(
        message.chat.id,
        f"🎁 Ты получил бонус +{format_balance(BONUS_AMOUNT)}!\n"
        f"💰 Новый баланс: {format_balance(new_balance)}",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(func=lambda message: message.text.startswith('🎲 Чёт'))
def button_even(message):
    try:
        bet_amount = int(message.text.split()[1])
    except:
        bet_amount = 100
    fake_message = message
    fake_message.text = f'/чёт {bet_amount}'
    place_bet(fake_message)

@bot.message_handler(func=lambda message: message.text.startswith('🎲 Нечет'))
def button_odd(message):
    try:
        bet_amount = int(message.text.split()[1])
    except:
        bet_amount = 100
    fake_message = message
    fake_message.text = f'/нечет {bet_amount}'
    place_bet(fake_message)

@bot.message_handler(func=lambda message: message.text.startswith('🃏 Джокер'))
def button_joker(message):
    parts = message.text.split()
    if len(parts) >= 3:
        bet_amount = int(parts[1])
        guessed = int(parts[2])
    else:
        bet_amount = 100
        guessed = 3
    fake_message = message
    fake_message.text = f'/джокер {bet_amount} {guessed}'
    place_bet(fake_message)

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
        f"💰 Твой баланс: {format_balance(current_balance)}\n\n"
        f"📊 Коэффициенты:\n"
        f"• Чёт/Нечет — x1.5\n"
        f"• Джокер (угадать число 1-6) — x3\n\n"
        f"⬇️ Используй кнопки ниже для игры!",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(commands=['balance'])
def balance(message):
    bal = get_balance(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"💰 Твой баланс: {format_balance(bal)}",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(commands=['bonus'])
def bonus(message):
    user_id = message.from_user.id
    new_balance = add_bonus(user_id)
    bot.send_message(
        message.chat.id,
        f"🎁 Ты получил бонус +{format_balance(BONUS_AMOUNT)}!\n"
        f"💰 Новый баланс: {format_balance(new_balance)}",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(commands=['чёт', 'нечет', 'джокер'])
def place_bet(message):
    user_id = message.from_user.id
    command = message.text.split()[0][1:]
    args = message.text.split()

    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Укажи сумму ставки в TON. Пример: /чёт 100",
            reply_markup=main_menu_keyboard()
        )
        return

    try:
        bet_amount = int(args[1])
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Сумма должна быть числом.",
            reply_markup=main_menu_keyboard()
        )
        return

    if bet_amount <= 0:
        bot.send_message(
            message.chat.id,
            "❌ Ставка должна быть больше 0 TON.",
            reply_markup=main_menu_keyboard()
        )
        return

    balance_now = get_balance(user_id)
    if bet_amount > balance_now:
        bot.send_message(
            message.chat.id,
            f"❌ Недостаточно средств! Твой баланс: {format_balance(balance_now)}",
            reply_markup=main_menu_keyboard()
        )
        return

    roll = random.randint(1, 6)
    win = False
    win_amount = 0

    if command == 'чёт':
        if roll in (2, 4, 6):
            win = True
            win_amount = int(bet_amount * 1.5)
        result_text = f"🎲 Выпало: {roll} (чётное)" if win else f"🎲 Выпало: {roll} (нечётное)"

    elif command == 'нечет':
        if roll in (1, 3, 5):
            win = True
            win_amount = int(bet_amount * 1.5)
        result_text = f"🎲 Выпало: {roll} (нечётное)" if win else f"🎲 Выпало: {roll} (чётное)"

    else:  # джокер
        if len(args) < 3:
            bot.send_message(
                message.chat.id,
                "❌ Для джокера укажи число от 1 до 6. Пример: /джокер 100 3",
                reply_markup=main_menu_keyboard()
            )
            return
        try:
            guessed = int(args[2])
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Введи число от 1 до 6.",
                reply_markup=main_menu_keyboard()
            )
            return
        if guessed < 1 or guessed > 6:
            bot.send_message(
                message.chat.id,
                "❌ Число должно быть от 1 до 6.",
                reply_markup=main_menu_keyboard()
            )
            return

        if roll == guessed:
            win = True
            win_amount = int(bet_amount * 3)
        result_text = f"🎲 Выпало: {roll}. Ты угадал!" if win else f"🎲 Выпало: {roll}. Ты не угадал."

    if win:
        update_balance(user_id, win_amount)
        bot.send_message(
            message.chat.id,
            f"✅ {result_text}\n"
            f"💰 Ты выиграл {format_balance(win_amount)}!\n"
            f"💳 Новый баланс: {format_balance(get_balance(user_id))}",
            reply_markup=main_menu_keyboard()
        )
    else:
        update_balance(user_id, -bet_amount)
        bot.send_message(
            message.chat.id,
            f"❌ {result_text}\n"
            f"💸 Ты проиграл {format_balance(bet_amount)}.\n"
            f"💳 Новый баланс: {format_balance(get_balance(user_id))}",
            reply_markup=main_menu_keyboard()
        )

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
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

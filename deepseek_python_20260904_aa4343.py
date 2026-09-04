import telebot
import random
import json
import os

TOKEN = '8969785862:AAGDi4NpAWB0Pm0BT3BsFMK6SiRKKGzvz7k'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'balances.json'
BONUS_AMOUNT = 2500
START_BALANCE = 2500

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

def main_menu_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('/balance')
    btn2 = telebot.types.KeyboardButton('/bonus')
    btn3 = telebot.types.KeyboardButton('/чёт 100')
    btn4 = telebot.types.KeyboardButton('/нечет 100')
    btn5 = telebot.types.KeyboardButton('/джокер 100 3')
    keyboard.add(btn1, btn2, btn3, btn4, btn5)
    return keyboard

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
    user_id = message.from_user.id
    command = message.text.split()[0][1:]
    args = message.text.split()

    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Укажи сумму ставки в TON. Пример: /чёт 100")
        return

    try:
        bet_amount = int(args[1])
    except ValueError:
        bot.send_message(message.chat.id, "❌ Сумма должна быть числом.")
        return

    if bet_amount <= 0:
        bot.send_message(message.chat.id, "❌ Ставка должна быть больше 0 TON.")
        return

    balance_now = get_balance(user_id)
    if bet_amount > balance_now:
        bot.send_message(
            message.chat.id,
            f"❌ Недостаточно средств! Твой баланс: {format_balance(balance_now)}"
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

    else:
        if len(args) < 3:
            bot.send_message(
                message.chat.id,
                "❌ Для джокера укажи число от 1 до 6. Пример: /джокер 100 3"
            )
            return
        try:
            guessed = int(args[2])
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введи число от 1 до 6.")
            return
        if guessed < 1 or guessed > 6:
            bot.send_message(message.chat.id, "❌ Число должно быть от 1 до 6.")
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
            f"💳 Новый баланс: {format_balance(get_balance(user_id))}"
        )
    else:
        update_balance(user_id, -bet_amount)
        bot.send_message(
            message.chat.id,
            f"❌ {result_text}\n"
            f"💸 Ты проиграл {format_balance(bet_amount)}.\n"
            f"💳 Новый баланс: {format_balance(get_balance(user_id))}"
        )

if __name__ == '__main__':
    print('🎰 TON Casino бот запущен...')
    bot.infinity_polling()
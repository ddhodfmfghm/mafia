# cd/d C:\Users\'имя пользователя'\AppData\Local\Programs\Python\'версия питона'\Scripts
# pip install pyTelegramBotAPI
    

import telebot
import random
from telebot import types

# Токен бота
TOKEN = ''

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Глобальные переменные для хранения состояния игры
players = {}
roles = []
game_state = "waiting"  # waiting, night, day
host_id = None

# Функция для создания клавиатуры для ведущего
def create_host_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔹 Присоединиться🔹'))
    markup.add(types.KeyboardButton('🫡 Ведущий🫡'))
    markup.add(types.KeyboardButton('👮🏻‍♂️ Начать игру👮🏻‍♂️'))
    markup.add(types.KeyboardButton('🌙 Ночь🌙'))
    markup.add(types.KeyboardButton('☀️ День☀️'))
    return markup

# Функция для создания клавиатуры для игроков
def create_player_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔹 Присоединиться🔹'))
    markup.add(types.KeyboardButton('🫡 Ведущий🫡'))
    return markup

# Функция для начала игры
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == host_id:
        bot.reply_to(message, 'Привет! Я бот для игры в мафию. Используйте /join для регистрации в игре.', reply_markup=create_host_keyboard())
    else:
        bot.reply_to(message, 'Привет! Я бот для игры в мафию. Используйте /join для регистрации в игре.', reply_markup=create_player_keyboard())

# Функция для регистрации игроков
@bot.message_handler(commands=['join'])
def join(message):
    player_name = message.from_user.username
    player_id = message.from_user.id
    if player_id not in players:
        players[player_id] = player_name
        if player_id == host_id:
            bot.reply_to(message, f'{player_name} присоединился к игре!', reply_markup=create_host_keyboard())
        else:
            bot.reply_to(message, f'{player_name} присоединился к игре!', reply_markup=create_player_keyboard())
    else:
        if player_id == host_id:
            bot.reply_to(message, f'{player_name}, вы уже в игре!', reply_markup=create_host_keyboard())
        else:
            bot.reply_to(message, f'{player_name}, вы уже в игре!', reply_markup=create_player_keyboard())

# Функция для назначения ведущего
@bot.message_handler(commands=['host'])
def set_host(message):
    global host_id
    host_id = message.from_user.id
    bot.reply_to(message, f'{message.from_user.username} назначен ведущим!', reply_markup=create_host_keyboard())

# Функция для начала игры
@bot.message_handler(commands=['begin'])
def begin_game(message):
    global game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может начать игру.', reply_markup=create_player_keyboard())
        return

    if len(players) < 2:
        bot.reply_to(message, 'Недостаточно игроков для начала игры.', reply_markup=create_host_keyboard())
        return

    # Распределение ролей
    roles.clear()
    num_mafia = len(players) // 2
    roles.extend(['мафия'] * num_mafia + ['мирный'] * (len(players) - num_mafia))
    random.shuffle(roles)

    # Отправка ролей игрокам
    for player_id, role in zip(players.keys(), roles):
        if player_id == host_id:
            bot.send_message(player_id, f'Ваша роль: {role}', reply_markup=create_host_keyboard())
        else:
            bot.send_message(player_id, f'Ваша роль: {role}', reply_markup=create_player_keyboard())

    # Отправка всех ролей ведущему
    roles_message = "\n".join([f'{players[player_id]}: {role}' for player_id, role in zip(players.keys(), roles)])
    bot.send_message(host_id, f'Роли игроков:\n{roles_message}', reply_markup=create_host_keyboard())

    game_state = "night"
    bot.send_message(message.chat.id, 'Игра началась! Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard())

# Функция для управления ночью
@bot.message_handler(commands=['night'])
def night(message):
    global game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может управлять ночью.', reply_markup=create_player_keyboard())
        return

    if game_state != "night":
        bot.reply_to(message, 'Сейчас не ночь.', reply_markup=create_host_keyboard())
        return

    # Логика для ночи (например, убийство)
    # ...

    game_state = "day"
    bot.send_message(message.chat.id, 'Наступил день. Все просыпаются!', reply_markup=create_host_keyboard())

# Функция для управления днем
@bot.message_handler(commands=['day'])
def day(message):
    global game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может управлять днем.', reply_markup=create_player_keyboard())
        return

    if game_state != "day":
        bot.reply_to(message, 'Сейчас не день.', reply_markup=create_host_keyboard())
        return

    # Логика для дня (например, голосование)
    # ...

    game_state = "night"
    bot.send_message(message.chat.id, 'Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard())

# Обработчик для текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == '🔹 Присоединиться🔹':
        join(message)
    elif message.text == '🫡 Ведущий🫡':
        set_host(message)
    elif message.text == '👮🏻‍♂️ Начать игру👮🏻‍♂️':
        begin_game(message)
    elif message.text == '🌙 Ночь🌙':
        night(message)
    elif message.text == '☀️ День☀️':
        day(message)
    else:
        if message.from_user.id == host_id:
            bot.reply_to(message, 'Неизвестная команда. Используйте кнопки для управления игрой.', reply_markup=create_host_keyboard())
        else:
            bot.reply_to(message, 'Неизвестная команда. Используйте кнопки для управления игрой.', reply_markup=create_player_keyboard())

# Основная функция для запуска бота
def main():
    bot.polling()

if __name__ == '__main__':
    main()


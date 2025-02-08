# cd/d C:\Users\'имя пользователя'\AppData\Local\Programs\Python\'версия питона'\Scripts (стандартное расположение)
# pip install pyTelegramBotAPI
    

import telebot
import random
from telebot import types

# Токен бота
TOKEN = '7452447929:AAH3U-8k5WBfoPbuqEW4G7FdMNPsOoBuysE'

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
    markup.add(types.KeyboardButton('👮🏻‍♂️ Начать игру👮🏻‍♂️'))
    markup.add(types.KeyboardButton('☀️ День'))
    markup.add(types.KeyboardButton('🌙 Ночь'))
    markup.add(types.KeyboardButton('🆕 Новая игра🆕'))
    markup.add(types.KeyboardButton('❌ Сбросить роль'))
    return markup

# Функция для создания клавиатуры для игроков
def create_player_keyboard(is_host_assigned=False, is_player=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if not is_host_assigned and not is_player:
        markup.add(types.KeyboardButton('🫡 Ведущий'))
    if not is_player:
        markup.add(types.KeyboardButton('🔹 Игрок🔹'))
    if is_player or is_host_assigned:
        markup.add(types.KeyboardButton('❌ Сбросить роль'))
    return markup

# Функция для начала игры
@bot.message_handler(commands=['start'])
def start(message):
    if host_id:
        bot.reply_to(message, 'Привет! Я бот для игры в мафию. Используйте кнопки для взаимодействия с игрой.', reply_markup=create_player_keyboard(is_host_assigned=True))
    else:
        bot.reply_to(message, 'Привет! Я бот для игры в мафию. Используйте кнопки для взаимодействия с игрой.', reply_markup=create_player_keyboard())

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
            bot.reply_to(message, f'{player_name} присоединился к игре!', reply_markup=create_player_keyboard(is_host_assigned=host_id is not None, is_player=True))
    else:
        if player_id == host_id:
            bot.reply_to(message, f'{player_name}, вы уже в игре!', reply_markup=create_host_keyboard())
        else:
            bot.reply_to(message, f'{player_name}, вы уже в игре!', reply_markup=create_player_keyboard(is_host_assigned=host_id is not None, is_player=True))

# Функция для назначения ведущего
@bot.message_handler(commands=['host'])
def set_host(message):
    global host_id
    player_id = message.from_user.id
    if host_id is not None:
        bot.reply_to(message, 'Ведущий уже назначен.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=player_id in players))
        return

    if player_id in players:
        bot.reply_to(message, 'Вы не можете стать ведущим, так как вы уже игрок.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
        return

    host_id = player_id
    bot.reply_to(message, f'{message.from_user.username} назначен ведущим!', reply_markup=create_host_keyboard())

    # Обновляем клавиатуру для всех игроков
    for player_id in players:
        if player_id != host_id:
            bot.send_message(player_id, 'Ведущий назначен.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))

# Функция для сброса ведущего
@bot.message_handler(commands=['resign'])
def resign_host(message):
    global host_id
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может сбросить свою роль.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return

    host_id = None
    bot.reply_to(message, 'Ведущий сброшен. Новый ведущий может быть назначен.', reply_markup=create_player_keyboard(is_player=message.from_user.id in players))

    # Обновляем клавиатуру для всех игроков
    for player_id in players:
        bot.send_message(player_id, 'Ведущий сброшен. Новый ведущий может быть назначен.', reply_markup=create_player_keyboard(is_player=True))

# Функция для сброса роли игрока
@bot.message_handler(commands=['reset_role'])
def reset_role(message):
    player_id = message.from_user.id
    if player_id in players:
        del players[player_id]
        bot.reply_to(message, 'Ваша роль сброшена.', reply_markup=create_player_keyboard(is_host_assigned=host_id is not None))
    elif player_id == host_id:
        resign_host(message)
    else:
        bot.reply_to(message, 'Вы не в игре.', reply_markup=create_player_keyboard(is_host_assigned=host_id is not None))

# Функция для начала игры
@bot.message_handler(commands=['begin'])
def begin_game(message):
    global game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может начать игру.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
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
            bot.send_message(player_id, f'Ваша роль: {role}', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))

    # Отправка всех ролей ведущему
    roles_message = "\n".join([f'{players[player_id]}: {role}' for player_id, role in zip(players.keys(), roles)])
    bot.send_message(host_id, f'Роли игроков:\n{roles_message}', reply_markup=create_host_keyboard())

    game_state = "night"
    for player_id in players:
        bot.send_message(player_id, 'Игра началась! Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))

# Функция для управления ночью
@bot.message_handler(commands=['night'])
def night(message):
    global game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может управлять ночью.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return

    if game_state != "day":
        bot.reply_to(message, 'Сейчас не день.', reply_markup=create_host_keyboard())
        return

    game_state = "night"
    for player_id in players:
        bot.send_message(player_id, 'Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))

# Функция для управления днем
@bot.message_handler(commands=['day'])
def day(message):
    global game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может управлять днем.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return
    if game_state != "night":
        bot.reply_to(message,'Сейчас не ночь.', reply_markup=create_host_keyboard())
        return

    game_state = "day"
    for player_id in players:
        bot.send_message(player_id, 'Наступил день. Все просыпаются! Начинается голосование.', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))

# Функция для начала новой игры
@bot.message_handler(commands=['newgame'])
def new_game(message):
    global players, roles, game_state
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может начать новую игру.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return

    players.clear()
    roles.clear()
    game_state = "waiting"
    bot.send_message(message.chat.id, 'Новая игра начата! Игроки могут присоединяться.', reply_markup=create_host_keyboard())

# Обработчик для текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == '🔹 Игрок🔹':
        join(message)
    elif message.text == '🫡 Ведущий':
        set_host(message)
    elif message.text == '👮🏻‍♂️ Начать игру👮🏻‍♂️':
        begin_game(message)
    elif message.text == '🌙 Ночь':
        night(message)
    elif message.text == '☀️ День':
        day(message)
    elif message.text == '🆕 Новая игра🆕':
        new_game(message)
    elif message.text == '❌ Сбросить роль':
        reset_role(message)
    else:
        if message.from_user.id == host_id:
            bot.reply_to(message, 'Неизвестная команда. Используйте кнопки для управления игрой.', reply_markup=create_host_keyboard())
        else:
            bot.reply_to(message, 'Неизвестная команда. Используйте кнопки для управления игрой.', reply_markup=create_player_keyboard(is_host_assigned=host_id is not None, is_player=message.from_user.id in players))

# Основная функция для запуска бота
def main():
    bot.polling()

if __name__ == '__main__':
    main()

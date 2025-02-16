import telebot
import random
from telebot import types

# Токен бота
TOKEN = ''

# Создание экземпляра бота
bot = telebot.TeleBot(TOKEN)

# Глобальные переменные для хранения состояния игры
all_users = []
players = {}
roles = {}
game_state = "waiting"  # waiting, night, day
host_id = None
victim_id = None
votes = {}  # Словарь для хранения голосов
voted_players = []  # Список для хранения проголосовавших игроков

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

# Функция для старта
@bot.message_handler(commands=['start'])
def start(message):
    if host_id:
        bot.reply_to(message, 'Привет! Я бот для игры в мафию. Используйте кнопки для взаимодействия с игрой.', reply_markup=create_player_keyboard(is_host_assigned=True))
    else:
        bot.reply_to(message, 'Привет! Я бот для игры в мафию. Используйте кнопки для взаимодействия с игрой.', reply_markup=create_player_keyboard())

# Функция для регистрации игроков
@bot.message_handler(commands=['join'])
def join(message):
    player_name = message.from_user.first_name
    player_id = message.from_user.id
    if player_id == host_id:
        bot.reply_to(message, 'Ведущий не может быть игроком. Сначала сбросьте роль ведущего.', reply_markup=create_host_keyboard())
        return
    if player_id not in players:
        players[player_id] = player_name
        bot.reply_to(message, f'{player_name} присоединился к игре!', reply_markup=create_player_keyboard(is_host_assigned=host_id is not None, is_player=True))
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
        bot.reply_to(message, 'Вы не можете стать ведущим, так как вы уже игрок. Сначала сбросьте роль игрока.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
        return

    host_id = player_id
    bot.reply_to(message, f'{message.from_user.first_name} назначен ведущим!', reply_markup=create_host_keyboard())

    # Обновление клавиатуры для всех игроков
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

    if game_state != "waiting":
        bot.reply_to(message, 'Вы не можете сбросить свою роль во время игры.')
        return

    host_id = None
    bot.reply_to(message, 'Ведущий сброшен. Новый ведущий может быть назначен.', reply_markup=create_player_keyboard(is_player=message.from_user.id in players))

    # Обновляем клавиатуру для всех игроков
    for player_id in players:
        bot.send_message(player_id, 'Ведущий сброшен. Новый ведущий может быть назначен.', reply_markup=create_player_keyboard(is_player=True))# Функция для сброса роли игрока

@bot.message_handler(commands=['reset_role'])
def reset_role(message):
    player_id = message.from_user.id
    if player_id in players:
        del players[player_id]
        if player_id in roles:  # Проверяем, существует ли ключ в словаре roles
            del roles[player_id]  # Удаляем роль игрока
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
    player_roles = ['мафия'] * num_mafia + ['мирный'] * (len(players) - num_mafia)
    random.shuffle(player_roles)

    # Назначение ролей игрокам
    for player_id, role in zip(players.keys(), player_roles):
        roles[player_id] = role
        if player_id == host_id:
            bot.send_message(player_id, f'Ваша роль: {role}', reply_markup=create_host_keyboard())
        else:
            bot.send_message(player_id, f'Ваша роль: {role}', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))

    # Отправка всех ролей ведущему
    roles_message = "\n".join([f'{players[player_id]}: {role}' for player_id, role in roles.items()])
    bot.send_message(host_id, f'Роли игроков:\n{roles_message}', reply_markup=create_host_keyboard())
    bot.send_message(host_id, 'Игра началась! Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard())

    game_state = "night"
    for player_id in players:
        bot.send_message(player_id, 'Игра началась! Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))

    # Отправка списка живых игроков мафии
    mafia_ids = [player_id for player_id, role in roles.items() if role == 'мафия']
    living_players = [players[player_id] for player_id in players.keys()]
    living_players_message = "\n".join([f'{i+1}. {name}' for i, name in enumerate(living_players)])
    for mafia_id in mafia_ids:
        bot.send_message(mafia_id, f'Выберите жертву:\n{living_players_message}', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))

# Функция для управления ночью
@bot.message_handler(commands=['night'])
def night(message):
    global game_state, victim_id
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может управлять ночью.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return

    if game_state != "day":
        bot.reply_to(message, 'Сейчас не день.', reply_markup=create_host_keyboard())
        return

    game_state = "night"
    for player_id in players:
        bot.send_message(player_id, 'Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))
    bot.send_message(host_id, 'Наступила ночь. Мафия, просыпайтесь!', reply_markup=create_host_keyboard())

    # Отправка списка живых игроков мафии
    mafia_ids = [player_id for player_id, role in roles.items() if role == 'мафия']
    living_players = [players[player_id] for player_id in players.keys()]
    living_players_message = "\n".join([f'{i+1}. {name}' for i, name in enumerate(living_players)])
    for mafia_id in mafia_ids:
        bot.send_message(mafia_id, f'Выберите жертву:\n{living_players_message}', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))

# Функция для управления днем
@bot.message_handler(commands=['day'])
def day(message):
    global game_state, victim_id, votes
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может управлять днем.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return
    if game_state != "night":
        bot.reply_to(message, 'Сейчас не ночь.', reply_markup=create_host_keyboard())
        return

    game_state = "day"
    if victim_id:
        victim_name = players[victim_id]
        # Уведомление убитого игрока о его смерти
        bot.send_message(victim_id, f'Вы были убиты мафией. Вы не можете больше играть до следующей игры.')
        del players[victim_id]  # Удаляем убитого игрока из списка игроков
        del roles[victim_id]  # Удаляем роль убитого игрока
        for player_id in players:
            bot.send_message(player_id, f'Наступил день. Все просыпаются! {victim_name} был убит мафией.', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))
        bot.send_message(host_id, f'Наступил день. Все просыпаются! {victim_name} был убит мафией.', reply_markup=create_host_keyboard())
        victim_id = None
        # Проверка на победу
        if all(role == 'мафия' for role in roles.values()):
            bot.send_message(host_id, 'Все мирные жители убиты. Мафия побеждает!')
            for player_id in players:
                bot.send_message(player_id, 'Все мирные жители убиты. Мафия побеждает!')
            game_state = "waiting"
            return
        elif 'мафия' not in roles.values():
            bot.send_message(host_id, 'Все мафиози исключены. Мирные жители побеждают!')
            for player_id in players:
                bot.send_message(player_id, 'Все мафиози исключены. Мирные жители побеждают!')
            game_state = "waiting"
            return
    else:
        for player_id in players:
            bot.send_message(player_id, 'Наступил день. Все просыпаются! Начинается голосование.', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))
        bot.send_message(host_id, 'Наступил день. Все просыпаются! Начинается голосование.', reply_markup=create_host_keyboard())

    # Начало голосования
    votes = {player_id: 0 for player_id in players}  # Сброс голосов
    voted_players.clear()  # Сброс списка проголосовавших
    living_players_message = "\n".join([f'{i+1}. {players[player_id]}' for i, player_id in enumerate(players.keys())])

    # Отправка сообщения о начале голосования всем живым игрокам
    for player_id in players:
        bot.send_message(player_id, f'Голосование началось! Выберите игрока, за которого хотите проголосовать:\n{living_players_message}')

# Обработчик для голосования
@bot.message_handler(func=lambda message: game_state == "day" and message.from_user.id in players)
def vote(message):
    global votes, voted_players
    player_id = message.from_user.id
    if player_id in voted_players:
        bot.reply_to(message, 'Вы уже проголосовали.')
        return

    try:
        vote_index = int(message.text) - 1
        if 0 <= vote_index < len(players):
            voted_player_id = list(players.keys())[vote_index]
            votes[voted_player_id] += 1
            voted_players.append(player_id)  # Добавляем игрока в список проголосовавших
            bot.reply_to(message, f'Вы проголосовали за {players[voted_player_id]}.')

            # Проверка, проголосовали ли все
            if len(voted_players) == len(players):
                # Подсчет голосов
                max_votes = max(votes.values())
                victims = [player for player, count in votes.items() if count == max_votes]
                if len(victims) == 1:
                    victim_id = victims[0]
                    victim_name = players[victim_id]  # Сохраняем имя жертвы
                    bot.send_message(victim_id, 'Вы были исключены из игры.')
                    del players[victim_id]  # Удаляем игрока из игры
                    del roles[victim_id]  # Удаляем роль игрока
                    bot.send_message(host_id, f'{victim_name} был исключен из игры.')  # Используем сохраненное имя

                    # Проверка на победу
                    if all(role == 'мафия' for role in roles.values()):
                        bot.send_message(host_id, 'Все мирные жители убиты. Мафия побеждает!')
                        for player_id in players:
                            bot.send_message(player_id, 'Все мирные жители убиты. Мафия побеждает!')
                        game_state = "waiting"
                    elif 'мафия' not in roles.values():
                        bot.send_message(host_id, 'Все мафиози исключены. Мирные жители побеждают!')
                        for player_id in players:
                            bot.send_message(player_id, 'Все мафиози исключены. Мирные жители побеждают!')
                        game_state = "waiting"
                else:
                    bot.send_message(host_id, 'Голосование завершено, но не удалось определить жертву.')
                # Переход к следующему этапу
                game_state = "night"
                for player_id in players:
                    bot.send_message(player_id, 'Голосование завершено.', reply_markup=create_host_keyboard() if player_id == host_id else create_player_keyboard(is_host_assigned=True, is_player=True))
        else:
            bot.reply_to(message, 'Неверный выбор. Попробуйте снова.')
    except ValueError:
        bot.reply_to(message, 'Пожалуйста, введите номер игрока, за которого хотите проголосовать.')

# Функция для начала новой игры
@bot.message_handler(commands=['newgame'])
def new_game(message):
    global players, roles, game_state, victim_id, votes, voted_players, host_id
    if message.from_user.id != host_id:
        bot.reply_to(message, 'Только ведущий может начать новую игру.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=message.from_user.id in players))
        return

    # Сброс всех глобальных переменных
    players.clear()
    roles.clear()
    game_state = "waiting"
    victim_id = None
    votes.clear()
    voted_players.clear()
    host_id = None  # Сброс ведущего

    # Отправка сообщения всем пользователям с новой клавиатурой
    for user_id in all_users:
        bot.send_message(user_id, 'Новая игра начата! Выберите свою роль.', reply_markup=create_player_keyboard())

# Обработчик для текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    global victim_id
    player_id = message.from_user.id

    # Добавляем пользователя в список всех пользователей, если его там нет
    if player_id not in all_users:
        all_users.append(player_id)

    if game_state == "night" and player_id in players:
        # Проверяем, что роли были назначены
        if player_id in roles:
            if roles[player_id] == 'мафия':
                try:
                    victim_index = int(message.text) - 1
                    if 0 <= victim_index < len(players):
                        victim_id = list(players.keys())[victim_index]
                        if victim_id == player_id:
                            bot.reply_to(message, 'Вы не можете убить себя. Выберите другую жертву.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
                        else:
                            bot.reply_to(message, f'Вы выбрали жертву: {players[victim_id]}', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
                            # Отправляем информацию ведущему о выбранной жертве
                            bot.send_message(host_id, f'Мафия выбрала жертву: {players[victim_id]}')
                    else:
                        bot.reply_to(message, 'Неверный выбор. Попробуйте снова.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
                except ValueError:
                    bot.reply_to(message, 'Пожалуйста, введите номер жертвы.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
        else:
            bot.reply_to(message, 'Роли еще не назначены. Пожалуйста, подождите.', reply_markup=create_player_keyboard(is_host_assigned=True, is_player=True))
    elif message.text == '🔹 Игрок🔹':
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

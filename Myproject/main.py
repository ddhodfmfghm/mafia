# cd/d C:\Users\'имя пользователя'\AppData\Local\Programs\Python\'версия питона'\Scripts
# pip install pyTelegramBotAPI



import telebot

bot = telebot.TeleBot('7452447929:AAH3U-8k5WBfoPbuqEW4G7FdMNPsOoBuysE')

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, 'Привет!')


bot.infinity_polling()

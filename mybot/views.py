from django.http import HttpResponse
from django.conf import settings
from telebot import TeleBot, types, logger

import logging

logger.setLevel(logging.DEBUG)

bot = TeleBot(settings.TOKEN)


def index(request):
    if request.method == 'GET':
        return HttpResponse('Bot is running')
    if request.method == 'POST':
        json_str = request.body.decode('UTF-8')
        update = types.Update.de_json(json_str)
        bot.process_new_updates([update])

        return HttpResponse(b'{"ok":true,"result":[]}')


# Клавиатуры

# Языковая клавиатура
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_ru = types.KeyboardButton('🇷🇺 Русский')
btn_uz = types.KeyboardButton('🇺🇿 Узбекский')
btn_en = types.KeyboardButton('🇺🇸 English')
main_keyboard.add(btn_ru, btn_uz, btn_en)


@bot.message_handler(commands=['start'])
def start_bot(message):

    greet_text = 'Здравствуйте. Это бот по продаже товаров\n\n' \
                 'Для продолжения, пожалуйста выберите язык:'

    bot.send_message(message.from_user.id, greet_text, reply_markup=main_keyboard)


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_message(message.chat.id, message.text.upper())

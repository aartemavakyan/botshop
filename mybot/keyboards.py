from telebot import types
import mybot.langmessages as messages_lang
from .models import Category

# Клавиатуры
# Клавиатура выбора языка
main_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
btn_ru = types.KeyboardButton('🇷🇺 Русский')
btn_en = types.KeyboardButton('🇺🇸 English')
btn_uz = types.KeyboardButton('🇺🇿 O\'zbek')
main_keyboard.add(btn_ru, btn_uz, btn_en)

# Главное меню
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_catalog = types.KeyboardButton('Каталог')
btn_cart = types.KeyboardButton('Корзина')
main_menu.row(btn_catalog)
main_menu.row(btn_cart)

# Кнопка НАЗАД
back_keyboard = types.InlineKeyboardMarkup()
back_keyboard.add(types.InlineKeyboardButton('Назад', callback_data='back_to_category'))

# Клавиатура корзины
cart_keyboard = types.InlineKeyboardMarkup()
cart_keyboard.row(types.InlineKeyboardButton('📝 Редактировать', callback_data='cart_edit'))
cart_keyboard.row(types.InlineKeyboardButton('💰 Оформить', callback_data='cart_pay'))

# Клавиатура с категориями
category_keyboard = types.InlineKeyboardMarkup()
cats = Category.objects.all()
for i in cats:
    category_keyboard.add(types.InlineKeyboardButton(i.name_ru, callback_data='btn_cat_' + str(i.id)))

# Клавиатура запроса номера телефона
phone_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
phone_keyboard.add(types.KeyboardButton(text='☎️ Отправить номер телефона ☎️', request_contact=True))




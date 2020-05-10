from django.http import HttpResponse
from django.conf import settings
from telebot import TeleBot, logger, types
from .models import Profile, Category, Product, Cart, CartItem, Order, OrderItem

# import logging
import mybot.keyboards as keyboards
import mybot.langmessages as messages_lang

# logger.setLevel(logging.DEBUG)

bot = TeleBot(settings.TOKEN)
bot.remove_webhook()
bot.set_webhook(settings.DOMAIN + settings.TOKEN + '/')

state = dict()
all_products = list()
is_first = True
count_to_cart = 1


def index(request):
    if request.method == 'GET':
        return HttpResponse('Bot is running')
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_str = request.body.decode('UTF-8')
            update = types.Update.de_json(json_str)
            bot.process_new_updates([update])
            return HttpResponse(b'{"ok":true,"result":[]}')
        else:
            return HttpResponse(b'{"ok":false,"result":[]}')


@bot.message_handler(commands=['start'])
def start_bot(message):
    greet_text = 'Здравствуйте. Это бот по продаже товаров\n\n' \
                 'Для продолжения, пожалуйста выберите язык:'
    bot.send_message(message.from_user.id, greet_text, reply_markup=keyboards.main_keyboard)

    # Создание пользователя при первом запуске
    try:
        obj = Profile.objects.get(external_id=message.from_user.id)
    except Profile.DoesNotExist:
        obj = Profile(
            external_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        obj.save()


@bot.message_handler(
    func=lambda message: message.text == '🇷🇺 Русский')
def ru_msg(message):
    bot.send_message(message.chat.id, 'Вы выбрали РУССКИЙ ЯЗЫК')
    bot.send_message(message.chat.id, 'Выберите пункт меню:', reply_markup=keyboards.main_menu)
    state.update({message.from_user.id: 'main'})


@bot.message_handler(func=lambda message: message.text == '🇺🇿 O\'zbek')
def uz_msg(message):
    bot.send_message(message.chat.id, 'Вы выбрали УЗБЕКСКИЙ')
    # TODO: Дописать узбекскую версию бота


@bot.message_handler(func=lambda message: message.text == '🇺🇸 English')
def en_msg(message):
    bot.send_message(message.chat.id, 'You choose ENGLISH')
    # TODO: Дописать английскую версию бота


@bot.message_handler(func=lambda message: message.text == 'Каталог')
def catalog(message):
    bot.send_message(message.chat.id, 'Выберите тип товара:', reply_markup=keyboards.category_keyboard)
    state.update({message.from_user.id: 'category'})


@bot.message_handler(func=lambda message: message.text == 'Корзина')
def cart(message):
    profile = Profile.objects.filter(external_id=message.from_user.id).first()
    cart = Cart.objects.filter(profile=profile).first()
    mes = ''
    if cart:
        for i in cart.cart_item.all():
            mes += f'{i.product.name_ru} * {i.count} {check_type(i)} = {i.all_price()} сум.\n'
        mes += f'---------------------\nИтого к оплате: {cart.all_sum()} сум.'
        bot.send_message(message.chat.id, 'У вас в корзине:\n---------------------\n' + mes, reply_markup=keyboards.cart_keyboard)
    else:
        bot.send_message(message.chat.id, '🤷‍♀️ Ваша корзина пуста 🤷‍♂️')
    state.update({message.from_user.id: 'incart'})


# Генерация ссылок на кнопки товаров
def gen_category_cb_name():
    cats = Category.objects.all()
    l = list()
    for i in cats:
        l.append('btn_cat_' + str(i.id))
    return l


def check_type(cart_item):
    if cart_item.product.type == 'pack':
        r = 'шт.'
    elif cart_item.product.type == 'kilo':
        r = 'кг.'
    elif cart_item.product.type == 'bottle':
        r = 'бут.'
    return r


@bot.callback_query_handler(func=lambda call: True and call.data in gen_category_cb_name())
def callback_category(call):
    global is_first
    cat_pk = call.data.split('_')[2]
    current_category = Category.objects.filter(id=cat_pk).get()
    products = Product.objects.filter(category=current_category)
    if not products:
        bot.edit_message_text(
            'К сожалению, товара данной категории НЕТ!',
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards.back_keyboard
        )
        bot.answer_callback_query(call.id)
        return
    all_products.clear()
    for i in products:
        all_products.append([i.id, i.name_ru, i.description_ru, i.price, i.image])
    is_first = True
    get_current_product(all_products, 1, call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)
    state.update({call.message.chat.id: 'look_for_product'})


# Генерация клавиатуры товара
def gen_product_keyboard(product_id, pos, cnt):
    product_keyboard = types.InlineKeyboardMarkup()
    product_keyboard.row(
        types.InlineKeyboardButton('⬅️', callback_data=f'product_prev_{cnt}_{pos}'),
        types.InlineKeyboardButton(str(pos) + ' из ' + str(cnt), callback_data=f'product_position_{cnt}_{pos}'),
        types.InlineKeyboardButton('➡️', callback_data=f'product_next_{cnt}_{pos}')
    )
    product_keyboard.row(
        types.InlineKeyboardButton('➕', callback_data=f'product_add_{cnt}_{pos}'),
        types.InlineKeyboardButton(count_to_cart, callback_data=f'product_count_{cnt}_{pos}'),
        types.InlineKeyboardButton('➖', callback_data=f'product_del_{cnt}_{pos}'),
    )
    product_keyboard.row(
        types.InlineKeyboardButton('🛒 Добавить в корзину', callback_data=f'product_item_{count_to_cart}_{product_id}')
    )
    return product_keyboard


def get_current_product(products, pos, id_chat, id_message):
    if products[pos - 1][4]:
        pic = products[pos - 1][4].open()

    global is_first

    if is_first:
        bot.send_photo(
            id_chat,
            pic,
            caption=products[pos - 1][1] + '\n' + products[pos - 1][2] + '\n\n' + str(
                products[pos - 1][3]) + ' сум',
            reply_markup=gen_product_keyboard(products[pos - 1][0], pos, len(products))
            )
    else:
        bot.edit_message_media(
            types.InputMediaPhoto(pic, products[pos - 1][1] + '\n' + products[pos - 1][2] + '\n\n' + str(
                products[pos - 1][3]) + ' сум'),
            id_chat,
            id_message,
            reply_markup=gen_product_keyboard(products[pos - 1][0], pos, len(products))
        )

    is_first = False


@bot.callback_query_handler(func=lambda call: True and call.data.startswith('product_'))
def next_prev_products(call):
    if call:
        global count_to_cart
        a = call.data.split('_')
        all_pr = int(a[2])
        cur_pr = int(a[3])
        if a[1] == 'next':
            count_to_cart = 1
            if all_pr == 1 and cur_pr == 1:
                bot.answer_callback_query(call.id)
                return
            elif all_pr == cur_pr and all_pr != 1 and cur_pr != 1:
                pos = 1
            else:
                pos = cur_pr + 1
            get_current_product(all_products, pos, call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        elif a[1] == 'prev':
            count_to_cart = 1
            if all_pr == 1 and cur_pr == 1:
                bot.answer_callback_query(call.id)
                return
            elif cur_pr == 1 and all_pr != 1:
                pos = all_pr
            else:
                pos = cur_pr - 1
            get_current_product(all_products, pos, call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        elif a[1] == 'position':
            bot.answer_callback_query(call.id)
            return
        elif a[1] == 'add':
            count_to_cart += 1
            get_current_product(all_products, cur_pr, call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        elif a[1] == 'del':
            if count_to_cart > 1:
                count_to_cart -= 1
                get_current_product(all_products, cur_pr, call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
        elif a[1] == 'item':
            pid = a[3]
            # Создаем cartItem
            product = Product.objects.get(pk=pid)
            profile = Profile.objects.get(external_id=call.message.chat.id)
            if profile and product:
                ci = CartItem.objects.filter(product=product, profile=profile).first()
                if ci:
                    ci.count += int(a[2])
                else:
                    ci = CartItem(profile=profile, product=product, count=a[2])
                ci.save()
                cart = Cart.objects.filter(profile=profile).first()
                if not cart:
                    cart = Cart(profile=profile)
                    cart.save()
                if ci not in cart.cart_item.all():
                    cart.cart_item.add(ci)
            count_to_cart = 1
            bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: True and call.data == 'back_to_category')
def back_to_category(call):
    bot.edit_message_text(
        'Выберите тип товара:',
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboards.category_keyboard
    )
    bot.answer_callback_query(call.id)
    state.update({call.message.chat.id: 'category'})


@bot.callback_query_handler(func=lambda call: True and call.data.startswith('cart_'))
def actions_in_cart(call):
    a = call.data.split('_')
    if a[1] == 'pay':
        bot.send_message(
            call.message.chat.id,
            text='Для продолжения оформления заказа вы должны отправить свой номер телефона',
            reply_markup=keyboards.phone_keyboard,
        )
        bot.answer_callback_query(call.id)


@bot.message_handler(content_types=['contact'])
def contact(message):
    if message.contact is not None:
        profile = Profile.objects.filter(external_id=message.from_user.id).first()
        if profile:
            profile.phone = message.contact.phone_number
            profile.first_name = message.contact.first_name
            profile.last_name = message.contact.last_name
            profile.save()

            # Перенос данных в таблицу заказов
            new_order = Order(profile=profile, cost=0, finished=False)
            new_order.save()

            cart_items = CartItem.objects.filter(profile=profile)
            if cart_items:
                for i in cart_items:
                    new_order_item = OrderItem(product=i.product, order=new_order, count=i.count,
                                               price=i.product.price*i.count)
                    new_order_item.save()

                    i.delete()

            total = 0
            for i in new_order.orderitem_set.all():
                total += i.price

            new_order.cost = total
            new_order.save()

            cart = Cart.objects.filter(profile=profile).first()
            if cart:
                cart.delete()

            bot.send_message(
                message.chat.id,
                'Спасибо за покупку. Курьер свяжется с вами в ближайшее время',
                reply_markup=keyboards.main_menu
            )


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    if state:
        if state[message.from_user.id] == 'lang':
            bot.send_message(message.chat.id, 'Вы должны выбрать язык')
        elif state[message.from_user.id] == 'main':
            bot.send_message(message.chat.id, 'Вы должны выбрать категорию')
        elif state[message.from_user.id] == 'category':
            bot.send_message(message.chat.id, 'Вы должны выбрать тип товара')
        elif state[message.from_user.id] == 'look_for_product':
            bot.send_message(message.chat.id, 'Просто выбирайте товар и добаляйте его в корзину')


# @bot.message_handler(func=lambda m: True)
# def echo_all(message):
#     bot.send_message(message.chat.id, message.text.upper())

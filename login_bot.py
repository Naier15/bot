import re
import secrets
import string
import sys
import os
import webbrowser
import logging

import telebot
from telebot import types
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bashni.settings')
import django
django.setup()
from django.contrib.auth.models import User
from authapp.models import UserProfile
from django.core.cache import cache
# from pprint import pprint

BOT_TOKEN = '1291275643:AAHIk28uq57pVT5ZZz-IEQllgQhP5_mwx7s'

PHONE = None
FIRST_NAME = None
USERNAME = None
EMAIL = None

bot = telebot.TeleBot(BOT_TOKEN)


logger_file = os.path.abspath(os.path.join(os.path.dirname(__file__), './login_bot.log'))
logging.basicConfig(
    level=logging.INFO, filename=logger_file, format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


@bot.message_handler(commands=['start', 'help'])
def main(message):
    btn =types.KeyboardButton('Разрешить', request_contact=True)
    delete = types.KeyboardButton('Отмена')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn, delete)
    text = 'Нажмите на кнопку "Разрешить" для разрешения доступа к вашему номеру телефона или "Отмена" если зашли по ошибке'
    bot.send_message(message.chat.id, text, reply_markup=markup)
    bot.register_next_step_handler(message, contact_handler)

@bot.message_handler()
def contact_handler(message):
    contact = message.contact
    keyboard = types.ReplyKeyboardRemove()
    if contact:
        phone_number = contact.phone_number.strip()
        bot.send_message(message.chat.id, f"Спасибо {message.contact.first_name}! Мы получили ваш номер телефона: "
                                          f"{phone_number}", reply_markup=keyboard)
        global PHONE
        if len(phone_number) == 11 and phone_number[0] == '7':
            PHONE = f'8{phone_number[1:]}'
        elif len(phone_number) == 12 and phone_number[0] == '+':
            PHONE = f'8{phone_number[2:]}'
        else:
            PHONE = phone_number

        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton('Авторизация', callback_data='auth')
        btn2 = types.InlineKeyboardButton('Регистрация', callback_data='reg')
        btn3 = types.InlineKeyboardButton('Отмена', callback_data='delete')
        markup.add(btn1, btn2, btn3)
        global FIRST_NAME, USERNAME
        FIRST_NAME = message.from_user.first_name
        USERNAME = message.from_user.username
        bot.send_message(message.chat.id, 'Выберите дальнейшее действие', reply_markup=markup)
    else:
        if message.text.strip() == 'Отмена':
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, message.text, reply_markup=keyboard)
        else:
            main(message)


@bot.callback_query_handler(func=lambda callback: True)
def callback_func(callback):
    if callback.data == 'delete':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)

    elif callback.data == 'auth':
        if PHONE:
            user_profile = UserProfile.objects.filter(tel=PHONE, is_company=False).first()
            if user_profile:
                # TelegramChat.objects.get_or_create(telegram_id=callback.message.chat.id,
                #                                    defaults={'user': user_profile.user})

                user = user_profile.user
                cache.set('telegram_user', user, 120)
                webbrowser.open('http://bashni.pro/')
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton('Перейти на bashni.pro', url='https://bashni.pro'
                )
                markup.add(btn1)
                bot.send_message(callback.message.chat.id, f'Вы авторизовались с логином {user.username} на '
                                                           f'портале bashni.pro', reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton(
                    'Регистрация', callback_data='reg'
                )
                btn2 = types.InlineKeyboardButton(
                    'Отмена', callback_data='delete'
                )
                markup.add(btn1, btn2)
                text = (f'Пользователь с номером телефона {PHONE} не найден в базе портала bashni.pro.\n'
                        f'Пройдите регистрацию.')
                bot.send_message(callback.message.chat.id, text, parse_mode='html', reply_markup=markup)

        else:
            main(callback.message)

    elif callback.data == 'reg':
        if PHONE:
            bot.send_message(callback.message.chat.id, 'Введите ваш почтовый ящик:')
            bot.register_next_step_handler(callback.message, check_email)
        else:
            main(callback.message)


def check_email(message):
    logger.info(f'user with tel: {PHONE} input email: {message.text}')
    if not re.match(r"^[A-Za-z0-9.+_-]+@[A-Za-z0-9._-]+\.[a-zA-Z]*$", message.text):
        bot.send_message(message.chat.id, 'Введенный текст не соответствует шаблону email. Повторите ввод:')
        bot.register_next_step_handler(message, check_email)

    else:
        user_email = User.objects.filter(email=message.text).first()
        if user_email:
            bot.send_message(message.chat.id, f'Почта {message.text} уже зарегистрирована на портале bashni.pro.\n'
                                              f'Попробуйте ввести другой email.')
            bot.register_next_step_handler(message, check_email)
        else:
            global EMAIL
            EMAIL = message.text
            user_profile = UserProfile.objects.filter(tel=PHONE).first()
            if not user_profile:
                alphabet = string.ascii_letters + string.digits
                temp_pass = ''.join(secrets.choice(alphabet) for _ in range(10))
                # username = 'user_'.join(secrets.choice(string.ascii_letters) for _ in range(8))
                try:
                    user = User.objects.filter(username=USERNAME).first()
                    if not user:
                        user = User(username=USERNAME, first_name=FIRST_NAME, email=EMAIL)
                        user.set_password(temp_pass)
                        user.save()
                        UserProfile.objects.get_or_create(tel=PHONE, defaults={'user': user})
                        # TelegramChat.objects.get_or_create(telegram_id=message.chat.id, defaults={'user': user})
                        text = (f'Вы успешно зарегистрировались.\nВаш логин на портале: {USERNAME}\n'
                                f'Пароль: {temp_pass}\nВы можете позже поменять их в личном кабинете')
                        btn1 = types.InlineKeyboardButton('Авторизация', callback_data='auth')
                        markup = types.InlineKeyboardMarkup()
                        markup.add(btn1)
                        logger.info(f'user: {user.username} добавлен в бд! Отображаю кнопку авторизации')
                        bot.send_message(message.chat.id, text, reply_markup=markup)
                    else:
                        UserProfile.objects.get_or_create(tel=PHONE, defaults={'user': user})
                        # TelegramChat.objects.get_or_create(telegram_id=message.chat.id, defaults={'user': user})
                        text = (f'В базе найден пользователь с логином {user.username} и привязанной к нему '
                                f'почтой {user.email}\nДелаю привязку телефона {PHONE} и создаю профиль пользователя.')
                        logger.info(f'{text}')
                        btn1 = types.InlineKeyboardButton('Авторизация', callback_data='auth')
                        markup = types.InlineKeyboardMarkup()
                        markup.add(btn1)
                        bot.send_message(message.chat.id, text, reply_markup=markup)

                except Exception as e:
                    # print('e = ', e)
                    # user = User(username=username, first_name=callback.message.from_user.first_name)
                    # user.set_password(temp_pass)
                    # user.save()
                    # UserProfile.objects.create(user=user, tel=PHONE)
                    # TelegramChat.objects.create(telegram_id=callback.message.chat.id, user=user)
                    # btn1 = types.InlineKeyboardButton(
                    #     'Авторизация', callback_data='auth'
                    # )
                    # text = (f'Вы успешно зарегистрировались.\nВаш логин на портале: {username}\n'
                    #         f'Пароль: {temp_pass}\nВы можете позже поменять их в личном кабинете')
                    # markup = types.InlineKeyboardMarkup()
                    # markup.add(btn1)
                    # bot.send_message(callback.message.chat.id, text, reply_markup=markup)
                    logger.error(f'error: {e}')
                    bot.send_message(message.chat.id, f'Ошибка регистрации: {e}\nПросим вас отправить скрин этой '
                                                      f'ошибки менеджеру bashni.pro')
            else:
                markup = types.InlineKeyboardMarkup()
                btn1 = types.InlineKeyboardButton(
                    'Авторизация', callback_data='auth'
                )
                btn2 = types.InlineKeyboardButton(
                    'Отмена', callback_data='delete'
                )
                markup.add(btn1, btn2)
                bot.send_message(message.chat.id,
                                 f'Пользователь {user_profile.user} с номером телефона {user_profile.tel} уже '
                                 f'зарегистрирован', reply_markup=markup)


bot.polling(none_stop=True)
from collections import deque
from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import emoji

from app.app import Context, App, Page
from app import text


router = Router()
context = Context()


@router.message(CommandStart())
async def start(msg: types.Message, state: FSMContext):
    btn = [[types.KeyboardButton(text='Разрешить', request_contact=True)]]
    markup = types.ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')
    await msg.answer(text.introduction, reply_markup=markup)
    await App.set_state(Page.menu, state)

# @router.message(Page.menu, F.contact)
# async def get_contact(msg: types.Message):
#     contact = msg.contact
#     await get_menu(msg)

@router.message(F.text == App.FLATS)
async def flats(msg: types.Message, state: FSMContext):
    btn = [[types.KeyboardButton(text=App.BACK)]]
    markup = types.ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')
    await msg.answer((
        'Каталог квартир интегрирован с сайтами застройщиков: актуальное наличие, цены застройщиков, бесплатное сопровождение от bashni.pro\n'
        '  1.	Выберите понравившуюся планировку\n'
        '  2.	Оставьте заявку\n'
        '  3.	Отдел продаж Bashni.pro назначает дату встречи\n'
        '  4.	Помощь с одобрением ипотеки\n'
        '  5.	Бронирование квартиры и выход на сделку\n'
        '  6.	Все услуги оказываются бесплатно\n'
        '  7.	Возможно онлайн встреча и сделка\n\n'
        'Перейти в каталог квартир\n\n'
        'Владивосток (https://bashni.pro/property/vladivostok/flats/)\n'
        'Уссурийск (https://bashni.pro/property/ussurijsk/flats/ )'
    ), reply_markup=markup)
    await App.set_state(Page.flats, state)

@router.message(F.text == App.OFFICES)
async def offices(msg: types.Message, state: FSMContext):
    btn = [[types.KeyboardButton(text=App.BACK)]]
    markup = types.ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')
    await msg.answer((
        'В каталоге представлены коммерческие помещения для ведения бизнеса в новостройках.\n'
        '  1.	Выберите понравившееся помещение\n'
        '  2.	Оставьте заявку\n'
        '  3.	Отдел продаж Bashni.pro назначает дату встречи\n'
        '  4.	Согласовываем условия оплаты\n'
        '  5.	Бронирование помещения и выход на сделку\n'
        '  6.	Все услуги оказываются бесплатно\n'
        'Возможно онлайн встреча и сделка\n\n'
        'Перейти в каталог помещений\n'
        'Владивосток (https://bashni.pro/property/vladivostok/commercial/ )'
    ), reply_markup=markup)
    await App.set_state(Page.offices, state)

@router.message(F.text == App.PROFILE)
async def profile(msg: types.Message, state: FSMContext):
    btn = [[types.KeyboardButton(text='Редактировать анкету')], [types.KeyboardButton(text=App.BACK)]]
    markup = types.ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')
    await msg.answer((
        '[эмодзи] Телефон\n'
        '[эмодзи] Логин\n'
        '[эмодзи] Email\n'
        '[эмодзи] Мой дом'
    ), reply_markup=markup)
    await App.set_state(Page.profile, state)

@router.message(F.text == App.SUBSCRIPTION)
async def subscription(msg: types.Message, state: FSMContext):
    btn = [[types.KeyboardButton(text='Новая подписка')], [types.KeyboardButton(text=App.BACK)]]
    markup = types.ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')
    await msg.answer('Бот, в котором можно задать вопросы менеджеру', reply_markup=markup)
    await App.set_state(Page.subscription, state)

@router.message(F.text == App.HELP)
async def help(msg: types.Message, state: FSMContext):
    btn = [[types.KeyboardButton(text=App.BACK)]]
    markup = types.ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True, input_field_placeholder='Выберете действие:')
    await msg.answer('Бот, в котором можно задать вопросы менеджеру', reply_markup=markup)
    await App.set_state(Page.help, state)

@router.message(F.text == App.BACK)
async def back(msg: types.Message, state: FSMContext):
    await App.go_back(state)
    await get_menu(msg)

@router.message(Page.menu)
async def get_menu(msg: types.Message):
    await msg.answer(App.MENU, reply_markup=App.menu())

# @router.message(F.text, Form.logined)
# async def start_questionnaire3(msg: types.Message, state: FSMContext):
#     await state.update_data(logined=msg.text)
#     await msg.answer('Мы закончили')

#     data = await state.get_data()
#     print(data)
#     await state.clear()
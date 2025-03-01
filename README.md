<h2 align="center">Telegram bot Bashni.pro</h2><br/>
Протестировано на версии python 3.13<br/><br/>

## Quick start
#### Настройки:
- в settings.py добавить `os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"`
- в settings.py в список INSTALLED_APPS добавить `bot`
- в django проекте запустить `git clone https://github.com/Naier15/bot`
- `python manage.py migrate` - установить миграцию из bot приложения
- `cd bot` - пройти в директорию бота и добавить файл `.env`
- в файле `.env` нужно указать следующие переменные:
`BOT_TOKEN = ...` - обязательная переменная - токен телеграм бота, запросы которого будет обслуживать приложение
`MANAGER_BOT_LINK = https://t.me/bashnipro_bot` - необязательная переменная - телеграм бот, на который будет указывать приложение в разделе Помощь
`DJANGO_HOST = https://bashni.pro/` - необязательная переменная - url сайта. Нужно изменить если url вдруг поменяется в будущем.
`REGION = Asia/Vladivostok` - необязательная переменная - часовой пояс, по времени которого будет происходить ежедневная рассылка новостей
<br/><br/>

#### Запуск бота:
- `cd bot` - перейти в папку с ботом
- `pip install -U pip` - обновить pip
- `pip install pipenv` - скачать проектный менеджер pipenv
- `pipenv shell` - активировать виртуальную среду
- `pipenv install` - установить все зависимости
- `pipenv run start` - запуск бота


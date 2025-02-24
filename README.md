<h2 align="center">Telegram bot Bashni.pro</h2><br/>
Протестировано на версии python 3.13<br/><br/>

## Quick start
### Настройки:
- в settings.py добавить `os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"`
- в settings.py в список INSTALLED_APPS добавить `bot`
- `git clone https://github.com/Naier15/bashni-bot`
- `python manage.py migrate` - установить миграцию из bot приложения
<br/><br/>
### Запуск бота:
- `cd bot` перейти в папку с ботом
- `pip install -U pip` - обновить pip
- `pip install pipenv` - скачать проектный менеджер pipenv
- `pipenv shell` - активировать виртуальную среду
- `pipenv install` - установить все зависимости
- `pipenv run start` - запуск бота
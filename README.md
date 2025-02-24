Quick start

Настройки:
- в settings.py добавить `os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"`
- в settings.py в список INSTALLED_APPS добавить `bot`
![Настройка](image-2.png)
- git clone ссылка на бота
- python manage.py migrate - установить миграцию из bot приложения

Запуск бота:
- cd bot - перейти в папку с ботом
- pip instal -U pip - обновить pip
- pip install pipenv - скачать проектный менеджер pipenv
- pipenv shell - активировать виртуальную среду
- pipenv install - установить все зависимости
- pipenv run start - запуск бота
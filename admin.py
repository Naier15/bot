from django.contrib import admin

try:
    from models import TgUser, SeenPhoto
except:
    from telegrambot.models import TgUser, SeenPhoto  # type: ignore


admin.site.register(TgUser)
admin.site.register(SeenPhoto)


from django.contrib import admin

from telegrambot.models import TgUser, SeenPhoto  # type: ignore


admin.site.register(TgUser)
admin.site.register(SeenPhoto)


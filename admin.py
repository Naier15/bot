from django.contrib import admin

from telegrambot.models import TgUser, SeenPhoto


admin.site.register(TgUser)
admin.site.register(SeenPhoto)


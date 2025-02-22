from django.db import models

from authapp.models import UserProfile
from property.models import Buildings


class Subscription(models.Model):
    chat_id = models.CharField(max_length = 12, verbose_name = 'chat_id', blank = False)
    send_keys = models.DateField(verbose_name = 'Выдача ключей', blank = True, null = True)
    user_profile = models.OneToOneField(UserProfile, on_delete = models.CASCADE)
    building = models.ManyToManyField(Buildings, verbose_name = 'building_id', blank = True)

    def __str__(self):
        return f'{self.id} ({self.user_profile.user.username})'

    class Meta:
        verbose_name_plural = 'Подписки telegram пользователей'
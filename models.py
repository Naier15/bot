from django.db import models

from authapp.models import UserProfile
from property.models import Buildings, BuildingPhotos


class SeenPhoto(models.Model):
    building = models.ForeignKey(Buildings, on_delete = models.CASCADE, verbose_name = 'Дом', blank = True)
    photo = models.ForeignKey(BuildingPhotos, on_delete = models.CASCADE, verbose_name = 'Ссылка на фото', blank = True)

    def __str__(self):
        return f'{self.building.id} ({self.photo.build_img})'

    class Meta:
        verbose_name_plural = 'Просмотренные фото'


class TgUser(models.Model):
    chat_id = models.CharField(max_length = 12, verbose_name = 'Чат', blank = False, unique = True)
    send_keys = models.DateField(verbose_name = 'Выдача ключей', blank = True, null = True)
    user_profile = models.OneToOneField(UserProfile, on_delete = models.CASCADE)
    is_registed = models.BooleanField(verbose_name = 'Зарегистрирован', default = False)
    building = models.ManyToManyField(Buildings, verbose_name = 'Дом', blank = True)
    seen_photos = models.ManyToManyField(SeenPhoto, verbose_name = 'Просмотренные фото', blank = True)

    def __str__(self):
        return f'{self.chat_id} ({self.user_profile.user.username})'

    class Meta:
        verbose_name_plural = 'telegram пользователи'
        ordering = ['id']

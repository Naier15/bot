from django.contrib import admin

from property.models import Buildings
from telegrambot.models import TgUser, SeenPhoto


admin.site.register(SeenPhoto)

@admin.register(TgUser)
class AdminTgUser(admin.ModelAdmin):
    @admin.display(description='User в БД')
    def view_user(self, obj):
        return obj.user_profile.user

    @admin.display(description='Дом (ЖК)')
    def get_buildings(self, obj):
        return [f'{b.num_dom} ({b.fk_property.name})' for b in obj.building.all()]

    list_display = ('id', 'chat_id', 'user_profile', 'view_user', 'get_buildings')
    search_fields = ['chat_id__contains', 'user_profile__user__first_name__icontains']
    search_help_text = 'чат id или user_profile'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "building":
            kwargs["queryset"] = Buildings.objects.order_by('fk_property__city', 'fk_property__name', 'num_dom')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

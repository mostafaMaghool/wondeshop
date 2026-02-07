from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from .serializers import *

# region Mostafa
@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = ('username', 'email', 'phone', 'is_staff', 'is_superuser', 'date_joined')
    list_filter  = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone',)}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('phone',)}),
    )

# admin.site.register(UserProfile)
# endregion
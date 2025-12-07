from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Uzytkownik

@admin.register(Uzytkownik)
class UzytkownikAdmin(UserAdmin):
    list_display = ("username", "imie", "nazwisko", "rola", "is_active")
    list_filter = ("rola", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Dodatkowe informacje", {"fields": ("rola", "imie", "nazwisko")}),
    )

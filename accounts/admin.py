from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Uzytkownik


@admin.action(description="Ustaw rolę: radny")
def action_set_role_radny(modeladmin, request, queryset):
    queryset.update(rola="radny")


@admin.action(description="Ustaw rolę: administrator")
def action_set_role_administrator(modeladmin, request, queryset):
    queryset.update(rola="administrator")


@admin.action(description="Ustaw rolę: prezydium")
def action_set_role_prezydium(modeladmin, request, queryset):
    queryset.update(rola="prezydium")


@admin.register(Uzytkownik)
class UzytkownikAdmin(UserAdmin):
    # Keep built-in auth admin behavior but expose custom fields
    fieldsets = UserAdmin.fieldsets + (
        (_("Dane e-SIR"), {"fields": ("imie", "nazwisko", "rola", "must_change_password")}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (_("Dane e-SIR"), {"fields": ("imie", "nazwisko", "rola", "must_change_password")}),
    )

    list_display = (
        "username",
        "imie",
        "nazwisko",
        "rola",
        "is_staff",
        "is_superuser",
        "is_active",
        "last_login",
    )
    list_filter = ("rola", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "imie", "nazwisko", "email")
    ordering = ("username",)

    actions = [
        action_set_role_radny,
        action_set_role_administrator,
        action_set_role_prezydium,
    ]

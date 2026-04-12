from django.contrib import admin

from .models import Komisja, KomisjaPunktObrad, KomisjaSesja, Obecnosc, PunktObrad, Sesja


class PunktObradInline(admin.TabularInline):
	model = PunktObrad
	extra = 0
	fields = ("numer", "tytul", "opis", "aktywny")


class ObecnoscInline(admin.TabularInline):
	model = Obecnosc
	extra = 0
	fields = ("radny", "obecny")
	autocomplete_fields = ("radny",)


@admin.register(Sesja)
class SesjaAdmin(admin.ModelAdmin):
	list_display = ("nazwa", "data", "aktywna", "opublikowana", "jest_usunieta")
	list_filter = ("aktywna", "opublikowana", "jest_usunieta")
	search_fields = ("nazwa", "opis")
	ordering = ("-data",)
	inlines = (PunktObradInline, ObecnoscInline)


class KomisjaPunktObradInline(admin.TabularInline):
	model = KomisjaPunktObrad
	extra = 0
	fields = ("numer", "tytul", "opis", "aktywny")


class KomisjaSesjaInline(admin.TabularInline):
	model = KomisjaSesja
	extra = 0
	fields = ("nazwa", "data", "aktywna")


@admin.register(Komisja)
class KomisjaAdmin(admin.ModelAdmin):
	list_display = ("nazwa", "aktywna", "przewodniczacy")
	list_filter = ("aktywna",)
	search_fields = ("nazwa", "opis", "przewodniczacy__username", "przewodniczacy__imie", "przewodniczacy__nazwisko")
	filter_horizontal = ("czlonkowie",)
	inlines = (KomisjaSesjaInline,)


@admin.register(KomisjaSesja)
class KomisjaSesjaAdmin(admin.ModelAdmin):
	list_display = ("komisja", "nazwa", "data", "aktywna")
	list_filter = ("aktywna", "komisja")
	search_fields = ("nazwa", "komisja__nazwa")
	ordering = ("-data",)
	inlines = (KomisjaPunktObradInline,)

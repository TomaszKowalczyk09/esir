from django.urls import path
from . import views

urlpatterns = [
    # Panel główny (przekierowuje wg roli)
    path("", views.panel, name="panel"),

    # PREZYDIUM
    path(
        "prezydium/dashboard/",
        views.prezydium_dashboard,
        name="prezydium_dashboard",
    ),
    path(
        "prezydium/sesje/",
        views.prezydium_sesje,
        name="prezydium_sesje",
    ),
    # Zakładka „Głosowania” prezydium
    path(
        "prezydium/",
        views.prezidium_panel,
        name="prezydium",
    ),
    path(
        "prezydium/porzadek-obrad/",
        views.porzadek_obrad_prezidium,
        name="porzadek_obrad_prezydium",
    ),
    path(
        "prezydium/nadchodzace-sesje/",
        views.nadchodzace_sesje_prezidium,
        name="nadchodzace_sesje_prezidium",
    ),

    # Operacje na sesjach
    path("sesje/nowa/", views.sesja_nowa, name="sesja_nowa"),
    path("sesje/<int:sesja_id>/edytuj/", views.sesja_edytuj, name="sesja_edytuj"),
    path(
        "sesje/<int:sesja_id>/ustaw-aktywna/",
        views.ustaw_sesje_aktywna,
        name="ustaw_sesje_aktywna",
    ),
    path(
        "sesje/<int:sesja_id>/dezaktywuj/",
        views.dezaktywuj_sesje,
        name="dezaktywuj_sesje",
    ),
    path(
        "sesje/<int:sesja_id>/usun/",
        views.usun_sesje,
        name="usun_sesje",
    ),

    # RADNY
    path("radny/", views.radny, name="radny"),
    path("radny/panel/", views.radny_panel, name="radny_panel"),

    # Głosowania – operacje wspólne
    path(
        "glosowanie/<int:glosowanie_id>/toggle/",
        views.toggle_glosowanie,
        name="toggle_glosowanie",
    ),
    path(
        "glosowanie/<int:glosowanie_id>/glosuj/",
        views.oddaj_glos,
        name="oddaj_glos",
    ),
    path(
        "api/wyniki/<int:glosowanie_id>/",
        views.api_wyniki,
        name="api_wyniki",
    ),
    path(
        "api/glosy-jawne/<int:glosowanie_id>/",
        views.api_lista_glosow_jawne,
        name="api_lista_glosow_jawne",
    ),

    # Pełnoekranowy ekran głosowania
    path("glosowanie/<int:glosowanie_id>/ekran/", views.glosowanie_ekran, name="glosowanie_ekran"),
    path("api/glosowanie/<int:glosowanie_id>/status/", views.api_glosowanie_status, name="api_glosowanie_status"),

    # Wyniki publiczne
    path("wyniki/", views.wyniki_publiczne, name="wyniki"),
    # Ekran sesji
    path("sesja/<int:sesja_id>/ekran/", views.sesja_ekran, name="sesja_ekran"),
    path("api/sesja/<int:sesja_id>/aktywny-punkt/", views.api_aktywny_punkt, name="api_aktywny_punkt"),
    path(
        "punkty/<int:punkt_id>/ustaw-aktywny/",
        views.ustaw_punkt_aktywny,
        name="ustaw_punkt_aktywny",
),
path(
    "prezydium/agenda/",
    views.prezydium_agenda,
    name="prezydium_agenda",
),
path(
    "punkty/<int:punkt_id>/ustaw-aktywny/",
    views.ustaw_punkt_aktywny,
    name="ustaw_punkt_aktywny",
),

    # WNIOSKI
    path("radny/wnioski/", views.wnioski_radny, name="wnioski_radny"),
    path("prezydium/wnioski/", views.wnioski_prezidium, name="wnioski_prezidium"),
    path("prezydium/wnioski/<int:wniosek_id>/zatwierdz/", views.wniosek_zatwierdz, name="wniosek_zatwierdz"),

    # OBECNOŚĆ / QUORUM
    path("prezydium/obecnosci/", views.obecnosci_prezidium, name="obecnosci_prezidium"),
    path("radny/obecnosc/", views.ustaw_obecnosc, name="ustaw_obecnosc"),
    path(
        "prezydium/sesja/<int:sesja_id>/obecnosci/<int:radny_id>/toggle/",
        views.obecnosci_toggle_prezidium,
        name="obecnosci_toggle_prezidium",
    ),

    # TESTY / reset danych
    path("prezydium/reset/", views.reset_danych_testowych, name="reset_danych_testowych"),
]

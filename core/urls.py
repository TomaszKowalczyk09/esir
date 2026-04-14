from django.urls import path
from django.views.generic import TemplateView  
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.shortcuts import redirect
from . import views

urlpatterns = [
            
    
    path("docs", lambda request: redirect('/docs/index.html')),
    path("docs/", lambda request: redirect('/docs/index.html')),
    re_path(r"^docs/(?P<section>[^/]+)/$", lambda request, section: redirect(f"/docs/{section}/index.html")),
        re_path(r"^docs/(?P<section>[^/]+)/$", lambda request, section: redirect(f"/docs/{section}/index.html")),
            path("api/ekran_komunikat/clear/", views.api_ekran_komunikat_clear, name="api_ekran_komunikat_clear"),
        
        path("api/ekran_komunikat/", views.api_ekran_komunikat, name="api_ekran_komunikat"),
    
    path("ekran/komunikat/", views.ekran_komunikat, name="ekran_komunikat"),
    path("ekran/komunikat/publiczny/", views.ekran_komunikat_publiczny, name="ekran_komunikat_publiczny"),
    
    path(
        "punkt/<int:punkt_id>/przesun/<str:kierunek>/",
        views.przesun_punkt_obrad,
        name="przesun_punkt_obrad",
    ),
    
    path(
        "punkt/<int:punkt_id>/usun/",
        views.usun_punkt_obrad,
        name="usun_punkt_obrad",
    ),
    path("protokol/wybor/", views.protokol_sesji_wybor, name="protokol_sesji_wybor"),
    path("protokol/pdf/", views.protokol_sesji_pdf_wybor, name="protokol_sesji_pdf_wybor"),
    
    path("", views.landing, name="landing"),
    
    path("panel/", views.panel, name="panel"),

    
    path("pomoc/", views.pomoc, name="pomoc"),
    path("identyfikator/", views.e_identyfikator, name="e_identyfikator"),

    
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

    
    path(
        "prezydium/radni/",
        views.prezydium_uczestnicy,
        name="prezydium_uczestnicy",
    ),
    path(
        "prezydium/radni/<int:user_id>/",
        views.prezydium_uczestnik_szczegoly,
        name="prezydium_uczestnik_szczegoly",
    ),

    
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

    
    path("radny/", views.radny, name="radny"),
    path("radny/panel/", views.radny_panel, name="radny_panel"),

    
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

    
    path("wyniki/", views.wyniki_publiczne, name="wyniki"),
    
    path("sesja/<int:sesja_id>/ekran/", views.sesja_ekran, name="sesja_ekran"),
    path("api/sesja/<int:sesja_id>/aktywny-punkt/", views.api_aktywny_punkt, name="api_aktywny_punkt"),
    path(
        "punkty/<int:punkt_id>/ustaw-aktywny/",
        views.ustaw_punkt_aktywny,
        name="ustaw_punkt_aktywny",
),
    path(
        "punkty/<int:punkt_id>/usun/",
        views.usun_punkt_obrad,
        name="usun_punkt_obrad",
    ),
path(
    "prezydium/agenda/",
    views.prezydium_agenda,
    name="prezydium_agenda",
),

    
    path("prezydium/protokol/pdf/", views.protokol_sesji_pdf, name="protokol_sesji_pdf"),

    
    path("radny/wnioski/", views.wnioski_radny, name="wnioski_radny"),
    path("radny/wnioski/pdf/", views.wnioski_radny_pdf, name="wnioski_radny_pdf"),
    path("wnioski/<int:wniosek_id>/pdf/", views.wniosek_pdf, name="wniosek_pdf"),
    path("prezydium/wnioski/", views.wnioski_prezidium, name="wnioski_prezidium"),
    path("prezydium/wnioski/<int:wniosek_id>/zatwierdz/", views.wniosek_zatwierdz, name="wniosek_zatwierdz"),

    
    path("prezydium/obecnosci/", views.obecnosci_prezidium, name="obecnosci_prezidium"),
    path("radny/obecnosc/", views.ustaw_obecnosc, name="ustaw_obecnosc"),
    path(
        "prezydium/sesja/<int:sesja_id>/obecnosci/<int:radny_id>/toggle/",
        views.obecnosci_toggle_prezidium,
        name="obecnosci_toggle_prezidium",
    ),

    
    path("prezydium/reset/", views.reset_danych_testowych, name="reset_danych_testowych"),

    
    path("komisje/", views.komisje_moje, name="komisje_moje"),
    path("komisje/utworz/", views.komisja_utworz, name="komisja_utworz"),
    path("komisje/<int:komisja_id>/", views.komisja_szczegoly, name="komisja_szczegoly"),
    path("komisje/<int:komisja_id>/sesje/<int:sesja_id>/edytuj/", views.komisja_sesja_edytuj, name="komisja_sesja_edytuj"),
    path("komisje/<int:komisja_id>/sesje/dodaj/", views.komisja_dodaj_sesje, name="komisja_dodaj_sesje"),
    path("komisje/<int:komisja_id>/czlonkowie/dodaj/", views.komisja_dodaj_czlonka, name="komisja_dodaj_czlonka"),
    path("komisje/<int:komisja_id>/czlonkowie/<int:user_id>/usun/", views.komisja_usun_czlonka, name="komisja_usun_czlonka"),
    path("komisje/<int:komisja_id>/wnioski/", views.komisja_wnioski, name="komisja_wnioski"),
    path("prezydium/komisje/skrzynka/", views.komisja_skrzynka_rady, name="komisja_skrzynka_rady"),
    path("prezydium/komisje/wniosek/<int:wniosek_id>/wyslij/", views.komisja_wniosek_wyslij_do_rady, name="komisja_wniosek_wyslij_do_rady"),

    
    path(
        "administrator/sesja/",
        views.admin_sesja_panel,
        name="admin_sesja_panel",
    ),

    
    path("ekran/sesja/", views.sesja_ekran_aktywna, name="sesja_ekran_aktywna"),
    path("ekran/sesja/<int:sesja_id>/", views.sesja_ekran, name="sesja_ekran_alias"),
]

if settings.DEBUG:
    urlpatterns += static("/docs/", document_root=settings.BASE_DIR / "core/static/docs")

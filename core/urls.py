from django.urls import path
from . import views

urlpatterns = [
    path('', views.panel, name='panel'),
    path('prezidium/', views.prezidium_panel, name='prezidium'),
    path('radny/', views.radny_panel, name='radny'),
    path('glosowanie/<int:glosowanie_id>/toggle/', views.toggle_glosowanie, name='toggle_glosowanie'),
    path('glosowanie/<int:glosowanie_id>/glosuj/', views.oddaj_glos, name='oddaj_glos'),
    path('api/wyniki/<int:glosowanie_id>/', views.api_wyniki, name='api_wyniki'),
    path('wyniki/', views.wyniki_publiczne, name='wyniki'),
    path('punkt/<int:punkt_id>/', views.punkt_ekran, name='punkt_ekran'),
    path('api/sesja/<int:sesja_id>/aktywny-punkt/', views.api_aktywny_punkt, name='api_aktywny_punkt'),
    path('sesja/<int:sesja_id>/ekran/', views.sesja_ekran, name='sesja_ekran'),
    path('sesja/<int:sesja_id>/aktywuj/', views.ustaw_sesje_aktywna, name='ustaw_sesje_aktywna'),
    path('punkt/<int:punkt_id>/aktywny/', views.ustaw_punkt_aktywny, name='ustaw_punkt_aktywny'),
    path('porzadek-obrad/', views.porzadek_obrad, name='porzadek_obrad'),
    path('prezydium/', views.prezidium_panel, name='prezidium'),
    path('sesja/<int:sesja_id>/usun/', views.usun_sesje, name='usun_sesje'),
    path('prezydium/porzadek-obrad/', views.porzadek_obrad_prezidium, name='porzadek_obrad_prezidium'),
    path('api/glosowanie/<int:glosowanie_id>/lista-glosow/', views.api_lista_glosow, name='api_lista_glosow'),
    path("nadchodzace-sesje/", views.nadchodzace_sesje, name="nadchodzace_sesje"),
    path("prezydium/porzadek-obrad/", views.porzadek_obrad_prezidium, name="porzadek_obrad_prezidium"),
    path("prezydium/nadchodzace-sesje/", views.nadchodzace_sesje_prezidium, name="nadchodzace_sesje_prezidium"),

]

# ESIR

System do obsługi sesji (porządku obrad) i głosowań w środowisku samorządowym – aplikacja webowa oparta o **Django 5.1**.

## Najważniejsze funkcje

- zarządzanie sesjami i porządkiem obrad (punkty obrad),
- głosowania (otwieranie/zamykanie, wyniki),
- wnioski powiązane z punktami obrad,
- obsługa komisji (powiązania: komisja–sesja, komisja–punkt, komisja–wniosek),
- panel dla prezydium/administratora oraz panel radnego,
- role użytkowników: **radny**, **prezydium**, **administrator**,
- proste statyczne zasoby i szablony HTML.

## Wymagania

- Python 3.x
- Django 5.1
- zależności w pliku `requirements.txt`

## Instalacja (Windows)

1. Utwórz i aktywuj wirtualne środowisko (venv).
2. Zainstaluj zależności z `requirements.txt`.
3. Wykonaj migracje bazy danych.
4. Uruchom serwer developerski.

> Projekt używa domyślnej bazy SQLite (`db.sqlite3`) – dobra do developmentu.

## Konfiguracja

- Główne ustawienia Django znajdują się w: `esir/settings.py`.
- Punkt wejścia do zarządzania projektem: `manage.py`.
- Aplikacje:
  - `accounts/` – użytkownicy i role,
  - `core/` – logika sesji, punktów obrad, głosowań, komisji, widoki i szablony.

### Role i uprawnienia (skrót)

- **radny** – widoki radnego (uczestnictwo w głosowaniach / podgląd),
- **prezydium** – dashboard i zarządzanie przebiegiem sesji,
- **administrator** – uprawnienia jak prezydium + czynności administracyjne.

## Uruchomienie

- Uruchom aplikację przez `manage.py`.
- Aplikacja startowa kieruje użytkownika do odpowiedniego panelu w zależności od roli.

## Struktura repozytorium (w skrócie)

- `accounts/` – model `Uzytkownik` (rola, imię, nazwisko, wymuszenie zmiany hasła)
- `core/` – modele: sesja, punkt obrad, głosowanie, głos, wniosek, komisje + formularze i widoki
- `core/templates/` – szablony HTML
- `static/` – pliki statyczne

## Testy

W repozytorium znajdują się pliki `tests.py` w aplikacjach `accounts` i `core`.

## Licencja

Kod źródłowy jest objęty licencją **All rights reserved** – szczegóły w pliku `LICENSE`.

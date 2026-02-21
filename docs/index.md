

# Dokumentacja projektu e-SIR

Witaj w dokumentacji projektu e-SIR!

## Opis
e-SIR to aplikacja Django do zarządzania sesjami, głosowaniami i użytkownikami w samorządzie.

---

## Instalacja
1. Sklonuj repozytorium:
	```bash
	git clone <adres-repozytorium>
	```
2. Zainstaluj zależności:
	```bash
	pip install -r requirements.txt
	```
3. Utwórz bazę danych:
	```bash
	python manage.py migrate
	```
4. Uruchom serwer:
	```bash
	python manage.py runserver
	```

---

## Konfiguracja
Wszystkie ustawienia znajdują się w pliku `esir/settings.py`. Kluczowe zmienne środowiskowe:
- `DJANGO_SECRET_KEY` – klucz bezpieczeństwa
- `DJANGO_DEBUG` – tryb debugowania
- `DJANGO_ALLOWED_HOSTS` – lista dozwolonych hostów

---

## Struktura projektu
- `accounts/` — moduł użytkowników
- `core/` — główny moduł aplikacji
- `e-sir/` — konfiguracja Django
- `static/` — pliki statyczne
- `docs/` — dokumentacja

---

## API
Wybrane endpointy:
- `/api/ekran_komunikat/` — pobieranie komunikatu globalnego
- `/api/ekran_komunikat/clear/` — czyszczenie komunikatu
- `/login/` — logowanie użytkownika
- `/panel/` — panel główny

---

## FAQ
**Jak dodać nowego użytkownika?**
Użyj panelu administratora lub polecenia `createsuperuser`.

**Jak uruchomić testy?**
```bash
python manage.py test
```

---

## Kontakt
W razie pytań skontaktuj się z administratorem projektu lub napisz na adres: admin@esir.pl

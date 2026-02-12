# Elektroniczny System Informacji i Rady (e-SIR)

System do obsługi głosowań dla **Młodzieżowej Rady Miejskiej w Gryfinie**.

## Bezpieczeństwo / dane w repo

Repozytorium jest publiczne. **Nie commituj danych osobowych ani haseł**.

- Plik `db.sqlite3` powinien być lokalny i **nie powinien trafiać do repozytorium**.
- Dane testowe twórz skryptami/komendami (np. `core/management/commands/dodaj_radnych.py`) z przykładowymi, fikcyjnymi danymi.

## PDF (polskie znaki)

Eksport wniosków do PDF używa fontów TrueType. Umieść pliki:

- `core/static/core/fonts/DejaVuSans.ttf`
- `core/static/core/fonts/DejaVuSans-Bold.ttf`

(DejaVuSans ma pełną obsługę polskich znaków.)

---

Projekt jest aplikacją webową opartą o **Django** (aplikacje: `accounts`, `core`) i domyślnie korzysta z bazy **SQLite** (`db.sqlite3`).

System umożliwia przygotowanie sesji głosowań, oddawanie głosów przez uprawnionych użytkowników oraz podgląd wyników.

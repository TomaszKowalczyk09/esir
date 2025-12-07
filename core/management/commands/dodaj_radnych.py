# core/management/commands/dodaj_radnych.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Uzytkownik
import string
import random

class Command(BaseCommand):
    help = 'Dodaje radnych do systemu'

    def handle(self, *args, **options):
        # Lista radnych: (imię, nazwisko, rola)
        radni_lista = [
            # Prezydium
            ('Izabella', 'Dolata', 'prezydium'),           # przewodnicząca
            ('Patryk', 'Mitręga', 'prezydium'),            # wiceprzewodniczący
            ('Maja', 'Świrbut', 'prezydium'),              # wiceprzewodnicząca

            # Zwykli radni
            ('Olga', 'Jangas', 'radny'),
            ('Jakub', 'Biernat', 'radny'),
            ('Michalina', 'Cirkosz', 'radny'),
            ('Maja', 'Golisowicz', 'radny'),
            ('Dawid', 'Gała', 'radny'),
            ('Filip', 'Rozworski', 'radny'),
            ('Gabriela', 'Żygadło', 'radny'),
            ('Laura', 'Ferens', 'radny'),
            ('Anna', 'Świtała', 'radny'),
            ('Julia', 'Staszak', 'radny'),
            ('Lena', 'Kokosza', 'radny'),
            ('Paula', 'Andrzejewska', 'radny'),
            ('Julia', 'Czajka', 'radny'),
            ('Piotr', 'Kauwa', 'radny'),
            ('Tomasz', 'Kowalczyk', 'radny'),
            ('Łukasz', 'Majka', 'radny'),
            ('Kacper', 'Romuk', 'radny'),
            ('Gabriela', 'Ulitko', 'radny'),
        ]

        utworzeni = []

        for imie, nazwisko, rola in radni_lista:
            # Generuj login
            login = f"{imie.lower()}.{nazwisko.lower()}"
            # Usuń znaki polskie
            login = login.replace('ł', 'l').replace('ó', 'o').replace('ę', 'e').replace('ą', 'a')
            login = login.replace('ć', 'c').replace('ż', 'z').replace('ź', 'z').replace('ś', 's').replace('ń', 'n')

            # Generuj losowe hasło (8 znaków)
            haslo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

            # Sprawdź, czy użytkownik już istnieje
            if User.objects.filter(username=login).exists():
                self.stdout.write(self.style.WARNING(f'Użytkownik {login} już istnieje, pomijam'))
                continue

            # Utwórz użytkownika
            user = User.objects.create_user(
                username=login,
                password=haslo,
                first_name=imie,
                last_name=nazwisko
            )

            # Utwórz profil Uzytkownik
            Uzytkownik.objects.create(user=user, rola=rola)

            utworzeni.append({
                'imie': imie,
                'nazwisko': nazwisko,
                'login': login,
                'haslo': haslo,
                'rola': rola
            })

            self.stdout.write(self.style.SUCCESS(f'✓ Dodano {imie} {nazwisko} ({rola})'))

        # Wyświetl tabelę
        self.stdout.write("\n" + "="*100)
        self.stdout.write(self.style.SUCCESS("TABELA LOGINÓW I HASEŁ"))
        self.stdout.write("="*100)
        self.stdout.write(f"{'Lp.':<5} {'Imię':<15} {'Nazwisko':<20} {'Login':<30} {'Hasło':<12} {'Rola':<15}")
        self.stdout.write("-"*100)

        for idx, u in enumerate(utworzeni, 1):
            self.stdout.write(f"{idx:<5} {u['imie']:<15} {u['nazwisko']:<20} {u['login']:<30} {u['haslo']:<12} {u['rola']:<15}")

        self.stdout.write("="*100)
        self.stdout.write(f"\nDodano {len(utworzeni)} użytkowników\n")

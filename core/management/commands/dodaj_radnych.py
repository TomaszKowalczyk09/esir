# core/management/commands/dodaj_radnych.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from accounts.models import Uzytkownik

import random
import string


def make_username(imie: str, nazwisko: str) -> str:
    # slugify -> ascii, lower, replaces spaces etc. Keep dot between parts.
    return f"{slugify(imie)}.{slugify(nazwisko)}"


class Command(BaseCommand):
    help = "Dodaje radnych do systemu"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nie zapisuje do bazy, tylko pokazuje co zostałoby utworzone.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # Lista: (imię, nazwisko, rola)
        radni_lista = [
            # II Kadencja – prezydium
            ("Izabella", "Dolata", "prezydium"),
            ("Patryk", "Mitręga", "prezydium"),
            ("Maja", "Świrbut", "prezydium"),
            ("Julia", "Czajka", "prezydium"),

            # II Kadencja – radni
            ("Olga", "Jangas", "radny"),
            ("Jakub", "Biernat", "radny"),
            ("Michalina", "Cirkosz", "radny"),
            ("Maja", "Golisowicz", "radny"),
            ("Dawid", "Gała", "radny"),
            ("Filip", "Rozworski", "radny"),
            ("Gabriela", "Żygadło", "radny"),
            ("Laura", "Ferens", "radny"),
            ("Anna", "Świtała", "radny"),
            ("Julia", "Staszak", "radny"),
            ("Lena", "Kokosza", "radny"),
            ("Paula", "Andrzejewska", "radny"),
            ("Piotr", "Kauwa", "radny"),
            ("Tomasz", "Kowalczyk", "radny"),
            ("Łukasz", "Majka", "radny"),
            ("Kacper", "Romuk", "radny"),
            ("Gabriela", "Ulitko", "radny"),        ]

        created = []
        skipped = []

        for imie, nazwisko, rola in radni_lista:
            username = make_username(imie, nazwisko)

            if Uzytkownik.objects.filter(username=username).exists():
                skipped.append((imie, nazwisko, username, rola))
                continue

            password = "".join(random.choices(string.ascii_letters + string.digits, k=10))

            if not dry_run:
                user = Uzytkownik.objects.create_user(
                    username=username,
                    password=password,
                    imie=imie,
                    nazwisko=nazwisko,
                    first_name=imie,
                    last_name=nazwisko,
                    rola=rola,
                    must_change_password=True,
                )
            else:
                user = None

            created.append((imie, nazwisko, username, password, rola))
            self.stdout.write(self.style.SUCCESS(f"✓ {('PLAN' if dry_run else 'Dodano')}: {imie} {nazwisko} ({rola}) -> {username}"))

        self.stdout.write("\n" + "=" * 110)
        self.stdout.write(self.style.SUCCESS("TABELA LOGINÓW I HASEŁ"))
        self.stdout.write("=" * 110)
        self.stdout.write(f"{'Lp.':<5} {'Imię':<15} {'Nazwisko':<22} {'Login':<32} {'Hasło':<14} {'Rola':<12}")
        self.stdout.write("-" * 110)

        for i, (imie, nazwisko, username, password, rola) in enumerate(created, 1):
            self.stdout.write(f"{i:<5} {imie:<15} {nazwisko:<22} {username:<32} {password:<14} {rola:<12}")

        self.stdout.write("=" * 110)
        self.stdout.write(f"\nUtworzono: {len(created)} | Pominięto (istniały): {len(skipped)}\n")

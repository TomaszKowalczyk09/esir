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
    help = "Dodaje użytkowników DEMO do systemu (bez danych osobowych)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nie zapisuje do bazy, tylko pokazuje co zostałoby utworzone.",
        )
        parser.add_argument(
            "--print-passwords",
            action="store_true",
            help="Wypisuje hasła na wyjściu (uwaga: nie używać na publicznych logach).",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=15,
            help="Ile kont DEMO utworzyć (radni).",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        print_passwords = options.get("print_passwords", False)
        count = options.get("count", 15)

        # KONTA DEMO (bez danych radnych). Prezydium = 1 konto.
        demo_users = [("Demo", "Prezydium", "prezydium")]
        for i in range(1, count + 1):
            demo_users.append(("Demo", f"Radny{i}", "radny"))

        created = []
        skipped = []

        for imie, nazwisko, rola in demo_users:
            username = make_username(imie, nazwisko)

            if Uzytkownik.objects.filter(username=username).exists():
                skipped.append((imie, nazwisko, username, rola))
                continue

            # dłuższe hasło, ale nie wypisujemy go domyślnie
            password = "".join(random.choices(string.ascii_letters + string.digits, k=16))

            if not dry_run:
                Uzytkownik.objects.create_user(
                    username=username,
                    password=password,
                    imie=imie,
                    nazwisko=nazwisko,
                    first_name=imie,
                    last_name=nazwisko,
                    rola=rola,
                    must_change_password=True,
                )

            created.append((imie, nazwisko, username, password, rola))
            self.stdout.write(self.style.SUCCESS(
                f"✓ {('PLAN' if dry_run else 'Dodano')}: {imie} {nazwisko} ({rola}) -> {username}"
            ))

        self.stdout.write("\n" + "=" * 110)
        if print_passwords:
            self.stdout.write(self.style.WARNING("TABELA LOGINÓW I HASEŁ (UWAGA: NIE PUBLIKUJ!)"))
        else:
            self.stdout.write(self.style.SUCCESS("TABELA LOGINÓW (hasła ukryte)"))
        self.stdout.write("=" * 110)

        if print_passwords:
            self.stdout.write(f"{'Lp.':<5} {'Imię':<15} {'Nazwisko':<22} {'Login':<32} {'Hasło':<20} {'Rola':<12}")
        else:
            self.stdout.write(f"{'Lp.':<5} {'Imię':<15} {'Nazwisko':<22} {'Login':<32} {'Rola':<12}")
        self.stdout.write("-" * 110)

        for i, (imie, nazwisko, username, password, rola) in enumerate(created, 1):
            if print_passwords:
                self.stdout.write(f"{i:<5} {imie:<15} {nazwisko:<22} {username:<32} {password:<20} {rola:<12}")
            else:
                self.stdout.write(f"{i:<5} {imie:<15} {nazwisko:<22} {username:<32} {rola:<12}")

        self.stdout.write("=" * 110)
        self.stdout.write(f"\nUtworzono: {len(created)} | Pominięto (istniały): {len(skipped)}\n")

from django.db import models
from accounts.models import Uzytkownik
from django.utils import timezone


class Sesja(models.Model):
    nazwa = models.CharField(max_length=200)
    data = models.DateTimeField(default=timezone.now)
    aktywna = models.BooleanField(default=True)
    jest_usunieta = models.BooleanField(default=False)  # NOWE POLE
    opublikowana = models.BooleanField(default=False)  # widoczna dla radnych przed startem

    def ustaw_aktywna(self):
        # dezaktywuj wszystkie inne sesje
        Sesja.objects.exclude(id=self.id).update(aktywna=False)
        self.aktywna = True
        jest_zamknieta = models.BooleanField(default=False)  # czy sesja zakończona
        jest_usunieta = models.BooleanField(default=False)  # miękkie usunięcie (soft delete)

        def zamknij(self):
            self.jest_zamknieta = True
            self.save()

        def usun(self):
            self.jest_usunieta = True
            self.save()

        self.save()

    def __str__(self):
        return self.nazwa

    class Meta:
        ordering = ["data"]


class PunktObrad(models.Model):
    sesja = models.ForeignKey(Sesja, on_delete=models.CASCADE, related_name='punkty')
    numer = models.IntegerField()
    tytul = models.CharField(max_length=300)
    opis = models.TextField(blank=True)
    aktywny = models.BooleanField(default=False)

    class Meta:
        ordering = ['numer']



    def __str__(self):
        return f"{self.numer}. {self.tytul}"


class Glosowanie(models.Model):
    JAWNOSC_CHOICES = [
        ("jawne", "Jawne"),
        ("tajne", "Tajne"),
    ]

    WIEKSZOSC_CHOICES = [
        ("zwykla", "Większość zwykła"),
        ("bezwzgledna", "Większość bezwzględna"),
    ]

    punkt_obrad = models.OneToOneField(PunktObrad, on_delete=models.CASCADE, related_name='glosowanie')
    nazwa = models.CharField(max_length=200)
    otwarte = models.BooleanField(default=False)
    utworzone = models.DateTimeField(auto_now_add=True)

    # nowe: typ głosowania
    jawnosc = models.CharField(max_length=10, choices=JAWNOSC_CHOICES, default="jawne")
    wiekszosc = models.CharField(max_length=15, choices=WIEKSZOSC_CHOICES, default="zwykla")
    liczba_uprawnionych = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Jeśli puste, system przyjmie liczbę oddanych głosów jako bazę dla większości bezwzględnej.",
    )

    def __str__(self):
        return self.nazwa

    def wynik_podsumowanie(self):
        """Zwraca słownik z wynikami oraz informacją czy uchwała/wniosek przeszedł.

        Uwaga: dla większości zwykłej przyjmujemy: ZA > PRZECIW.
        Dla większości bezwzględnej: ZA > (uprawnieni/2).
        """
        from .models import Glos  # uniknięcie importu cyklicznego

        za = Glos.objects.filter(glosowanie=self, glos="za").count()
        przeciw = Glos.objects.filter(glosowanie=self, glos="przeciw").count()
        wstrzymuje = Glos.objects.filter(glosowanie=self, glos="wstrzymuje").count()

        if self.wiekszosc == "zwykla":
            przeszedl = za > przeciw
            prog = None
        else:
            baza = self.liczba_uprawnionych
            if baza is None:
                baza = za + przeciw + wstrzymuje
            prog = (baza // 2) + 1
            przeszedl = za >= prog

        return {
            "za": za,
            "przeciw": przeciw,
            "wstrzymuje": wstrzymuje,
            "przeszedl": przeszedl,
            "prog": prog,
        }


class Glos(models.Model):
    glosowanie = models.ForeignKey(Glosowanie, on_delete=models.CASCADE)
    uzytkownik = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE)
    glos = models.CharField(max_length=10,
                            choices=[('za', 'Za'), ('przeciw', 'Przeciw'), ('wstrzymuje', 'Wstrzymuję się')])

    class Meta:
        unique_together = ['glosowanie', 'uzytkownik']
        ordering = ['uzytkownik']


class Wniosek(models.Model):
    TYP_CHOICES = [
        ("wniosek", "Wniosek"),
        ("zwo_sesji", "Zwołanie sesji"),
        ("proj_uchwaly", "Projekt uchwały"),
        ("zapytanie", "Zapytanie"),
    ]

    punkt_obrad = models.ForeignKey(
        PunktObrad,
        on_delete=models.CASCADE,
        related_name='wnioski',
        null=True,
        blank=True,
        help_text="Jeśli puste, wniosek jest złożony poza sesją.",
    )
    radny = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE)

    # automatyczna sygnatura, np. W/2026/0012
    sygnatura = models.CharField(max_length=32, unique=True, blank=True)

    tresc = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    zatwierdzony = models.BooleanField(default=False)
    typ = models.CharField(max_length=20, choices=TYP_CHOICES, default="wniosek")

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        sig = self.sygnatura or "(bez sygnatury)"
        return f"{sig} - {self.radny} - {self.tresc[:50]}"

    def _next_sygnatura(self):
        year = timezone.localdate().year
        prefix = f"W/{year}/"
        last = (
            Wniosek.objects.filter(sygnatura__startswith=prefix)
            .order_by("-sygnatura")
            .values_list("sygnatura", flat=True)
            .first()
        )
        if not last:
            n = 1
        else:
            try:
                n = int(last.split("/")[-1]) + 1
            except Exception:
                n = 1
        return f"{prefix}{n:04d}"

    def save(self, *args, **kwargs):
        if not self.sygnatura:
            # prosta generacja sygnatury; przy ewentualnym konflikcie dociągamy kolejną
            for _ in range(20):
                cand = self._next_sygnatura()
                if not Wniosek.objects.filter(sygnatura=cand).exists():
                    self.sygnatura = cand
                    break
            else:
                raise ValueError("Nie udało się wygenerować unikalnej sygnatury wniosku")
        super().save(*args, **kwargs)


class Obecnosc(models.Model):
    sesja = models.ForeignKey(Sesja, on_delete=models.CASCADE, related_name="obecnosci")
    radny = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE, related_name="obecnosci")
    obecny = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["sesja", "radny"]
        ordering = ["radny__nazwisko", "radny__imie"]

    def __str__(self):
        return f"{self.radny} @ {self.sesja} = {'obecny' if self.obecny else 'nieobecny'}"


class Komisja(models.Model):
    nazwa = models.CharField(max_length=200)
    opis = models.TextField(blank=True)
    przewodniczacy = models.ForeignKey(
        Uzytkownik,
        on_delete=models.PROTECT,
        related_name="komisje_przewodniczy",
        limit_choices_to={"rola": "radny"},
    )
    czlonkowie = models.ManyToManyField(
        Uzytkownik,
        related_name="komisje",
        blank=True,
        limit_choices_to={"rola": "radny"},
    )
    aktywna = models.BooleanField(default=True)

    class Meta:
        ordering = ["nazwa"]

    def __str__(self):
        return self.nazwa


class KomisjaSesja(models.Model):
    komisja = models.ForeignKey(Komisja, on_delete=models.CASCADE, related_name="sesje")
    nazwa = models.CharField(max_length=200)
    data = models.DateTimeField(default=timezone.now)
    aktywna = models.BooleanField(default=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.komisja.nazwa}: {self.nazwa}"


class KomisjaPunktObrad(models.Model):
    sesja = models.ForeignKey(KomisjaSesja, on_delete=models.CASCADE, related_name="punkty")
    numer = models.IntegerField()
    tytul = models.CharField(max_length=300)
    opis = models.TextField(blank=True)
    aktywny = models.BooleanField(default=False)

    class Meta:
        ordering = ["numer"]

    def __str__(self):
        return f"{self.numer}. {self.tytul}"


class KomisjaWniosek(models.Model):
    TYP_CHOICES = [
        ("wniosek", "Wniosek"),
        ("zapytanie", "Zapytanie"),
        ("postulat", "Postulat"),
    ]

    komisja = models.ForeignKey(Komisja, on_delete=models.CASCADE, related_name="wnioski")
    sesja = models.ForeignKey(KomisjaSesja, on_delete=models.SET_NULL, null=True, blank=True)
    punkt_obrad = models.ForeignKey(KomisjaPunktObrad, on_delete=models.SET_NULL, null=True, blank=True)

    autor = models.ForeignKey(Uzytkownik, on_delete=models.PROTECT, related_name="komisja_wnioski")
    typ = models.CharField(max_length=20, choices=TYP_CHOICES, default="wniosek")
    tresc = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    # workflow do "centrali" (rada)
    wyslany_do_rady = models.BooleanField(default=False)
    data_wyslania = models.DateTimeField(null=True, blank=True)
    zatwierdzony_przez_prezydium = models.BooleanField(default=False)
    data_zatwierdzenia = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_typ_display()} ({self.komisja})"

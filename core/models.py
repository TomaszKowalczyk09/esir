from django.db import models
from accounts.models import Uzytkownik
from django.utils import timezone

class Kandydat(models.Model):
    imie = models.CharField(max_length=100)
    nazwisko = models.CharField(max_length=100)
    punkt_obrad = models.ForeignKey('PunktObrad', on_delete=models.CASCADE, related_name='kandydaci')
    opis = models.TextField(blank=True)

    class Meta:
        verbose_name = "Kandydat"
        verbose_name_plural = "Kandydaci"

    def __str__(self):
        return f"{self.nazwisko} {self.imie}"


class Sesja(models.Model):
    nazwa = models.CharField(max_length=200)
    data = models.DateTimeField(default=timezone.now)
    opis = models.TextField(blank=True)
    aktywna = models.BooleanField(default=True)
    jest_usunieta = models.BooleanField(default=False)
    opublikowana = models.BooleanField(default=False)
    przerwa_start = models.DateTimeField(null=True, blank=True)
    przerwa_czas = models.IntegerField(null=True, blank=True, help_text="Czas przerwy w sekundach")
    jest_zamknieta = models.BooleanField(default=False)

    class Meta:
        ordering = ["data"]
        verbose_name = "Sesja"
        verbose_name_plural = "Sesje"

    def __str__(self):
        return self.nazwa

    def ustaw_aktywna(self):
        # dezaktywuj wszystkie inne sesje
        Sesja.objects.exclude(id=self.id).update(aktywna=False)
        self.aktywna = True
        self.save()

    def zamknij(self):
        self.jest_zamknieta = True
        self.save()

    def usun(self):
        self.jest_usunieta = True
        self.save()


class PunktObrad(models.Model):
    sesja = models.ForeignKey(Sesja, on_delete=models.CASCADE, related_name='punkty')
    numer = models.IntegerField()
    tytul = models.CharField(max_length=300)
    opis = models.TextField(blank=True)
    aktywny = models.BooleanField(default=False)

    class Meta:
        ordering = ['numer']
        verbose_name = "Punkt obrad"
        verbose_name_plural = "Punkty obrad"

    @property
    def glosowanie(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("glosowania")
        if prefetched is not None:
            if not prefetched:
                return None
            otwarte = [g for g in prefetched if g.otwarte]
            src = otwarte if otwarte else prefetched
            return sorted(src, key=lambda g: (g.utworzone, g.id), reverse=True)[0]
        return self.glosowania.order_by("-otwarte", "-utworzone", "-id").first()

    def __str__(self):
        return f"{self.numer}. {self.tytul}"


class Glosowanie(models.Model):
    JAWNOSC_CHOICES = [("jawne", "Jawne"), ("tajne", "Tajne")]
    WIEKSZOSC_CHOICES = [("zwykla", "Większość zwykła"), ("bezwzgledna", "Większość bezwzględna")]
    TYP_CHOICES = [("zwykle", "Zwykłe (za/przeciw/wstrzymuje)"), ("kandydaci", "Imienne na kandydata")]

    punkt_obrad = models.ForeignKey(PunktObrad, on_delete=models.CASCADE, related_name='glosowania')
    nazwa = models.CharField(max_length=200)
    otwarte = models.BooleanField(default=False)
    utworzone = models.DateTimeField(auto_now_add=True)
    typ = models.CharField(max_length=20, choices=TYP_CHOICES, default="zwykle")
    jawnosc = models.CharField(max_length=10, choices=JAWNOSC_CHOICES, default="jawne")
    wiekszosc = models.CharField(max_length=15, choices=WIEKSZOSC_CHOICES, default="zwykla")
    liczba_uprawnionych = models.PositiveIntegerField(null=True, blank=True)
    kandydaci = models.ManyToManyField(Kandydat, blank=True, related_name='glosowania')

    class Meta:
        verbose_name = "Głosowanie"
        verbose_name_plural = "Głosowania"

    def __str__(self):
        return self.nazwa

    def wynik_podsumowanie(self):
        za = Glos.objects.filter(glosowanie=self, glos="za").count()
        przeciw = Glos.objects.filter(glosowanie=self, glos="przeciw").count()
        wstrzymuje = Glos.objects.filter(glosowanie=self, glos="wstrzymuje").count()

        if self.wiekszosc == "zwykla":
            przeszedl = za > przeciw
            prog = None
        else:
            baza = self.liczba_uprawnionych or (za + przeciw + wstrzymuje)
            prog = (baza // 2) + 1
            przeszedl = za >= prog

        return {"za": za, "przeciw": przeciw, "wstrzymuje": wstrzymuje, "przeszedl": przeszedl, "prog": prog}


class Glos(models.Model):
    glosowanie = models.ForeignKey(Glosowanie, on_delete=models.CASCADE)
    uzytkownik = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE)
    glos = models.CharField(max_length=10, choices=[('za', 'Za'), ('przeciw', 'Przeciw'), ('wstrzymuje', 'Wstrzymuję się')], blank=True, null=True)
    kandydat = models.ForeignKey('Kandydat', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ['glosowanie', 'uzytkownik']
        ordering = ['uzytkownik']
        verbose_name = "Głos"
        verbose_name_plural = "Głosy"


class Wniosek(models.Model):
    TYP_CHOICES = [("wniosek", "Wniosek"), ("zwo_sesji", "Zwołanie sesji"), ("proj_uchwaly", "Projekt uchwały"), ("zapytanie", "Zapytanie")]
    punkt_obrad = models.ForeignKey(PunktObrad, on_delete=models.CASCADE, related_name='wnioski', null=True, blank=True)
    radny = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE)
    sygnatura = models.CharField(max_length=32, unique=True, blank=True)
    tresc = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    zatwierdzony = models.BooleanField(default=False)
    typ = models.CharField(max_length=20, choices=TYP_CHOICES, default="wniosek")

    class Meta:
        ordering = ["-data"]
        verbose_name = "Wniosek"
        verbose_name_plural = "Wnioski"

    def __str__(self):
        sig = self.sygnatura or "(bez sygnatury)"
        return f"{sig} - {self.radny} - {self.tresc[:50]}"

    def save(self, *args, **kwargs):
        if not self.sygnatura:
            year = timezone.localdate().year
            prefix = f"W/{year}/"
            last = Wniosek.objects.filter(sygnatura__startswith=prefix).order_by("-sygnatura").values_list("sygnatura", flat=True).first()
            n = (int(last.split("/")[-1]) + 1) if last else 1
            self.sygnatura = f"{prefix}{n:04d}"
        super().save(*args, **kwargs)


class Obecnosc(models.Model):
    sesja = models.ForeignKey(Sesja, on_delete=models.CASCADE, related_name="obecnosci")
    radny = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE, related_name="obecnosci")
    obecny = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["sesja", "radny"]
        ordering = ["radny__nazwisko", "radny__imie"]
        verbose_name = "Obecność"
        verbose_name_plural = "Obecności"

    def __str__(self):
        return f"{self.radny} @ {self.sesja} = {'obecny' if self.obecny else 'nieobecny'}"


class Komisja(models.Model):
    nazwa = models.CharField(max_length=200)
    opis = models.TextField(blank=True)
    przewodniczacy = models.ForeignKey(Uzytkownik, on_delete=models.PROTECT, related_name="komisje_przewodniczy", limit_choices_to={"rola": "radny"})
    czlonkowie = models.ManyToManyField(Uzytkownik, related_name="komisje", blank=True, limit_choices_to={"rola": "radny"})
    aktywna = models.BooleanField(default=True)

    class Meta:
        ordering = ["nazwa"]
        verbose_name = "Komisja"
        verbose_name_plural = "Komisje"

    def __str__(self):
        return self.nazwa


class KomisjaSesja(models.Model):
    komisja = models.ForeignKey(Komisja, on_delete=models.CASCADE, related_name="sesje")
    nazwa = models.CharField(max_length=200)
    data = models.DateTimeField(default=timezone.now)
    aktywna = models.BooleanField(default=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "Sesja komisji"
        verbose_name_plural = "Sesje komisji"

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
        verbose_name = "Punkt obrad komisji"
        verbose_name_plural = "Punkty obrad komisji"

    def __str__(self):
        return f"{self.numer}. {self.tytul}"

    @property
    def glosowanie(self):
        return self.glosowania.order_by("-otwarte", "-utworzone", "-id").first()


class KomisjaGlosowanie(models.Model):
    JAWNOSC_CHOICES = [("jawne", "Jawne"), ("tajne", "Tajne")]
    WIEKSZOSC_CHOICES = [("zwykla", "Większość zwykła"), ("bezwzgledna", "Większość bezwzględna")]
    punkt_obrad = models.ForeignKey(KomisjaPunktObrad, on_delete=models.CASCADE, related_name="glosowania")
    nazwa = models.CharField(max_length=200)
    otwarte = models.BooleanField(default=False)
    utworzone = models.DateTimeField(auto_now_add=True)
    jawnosc = models.CharField(max_length=10, choices=JAWNOSC_CHOICES, default="jawne")
    wiekszosc = models.CharField(max_length=15, choices=WIEKSZOSC_CHOICES, default="zwykla")
    liczba_uprawnionych = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-utworzone"]
        verbose_name = "Głosowanie komisji"
        verbose_name_plural = "Głosowania komisji"

    def __str__(self):
        return self.nazwa


class KomisjaGlos(models.Model):
    glosowanie = models.ForeignKey(KomisjaGlosowanie, on_delete=models.CASCADE, related_name="glosy")
    uzytkownik = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE, related_name="komisja_glosy")
    glos = models.CharField(max_length=10, choices=[("za", "Za"), ("przeciw", "Przeciw"), ("wstrzymuje", "Wstrzymuję się")])

    class Meta:
        unique_together = ["glosowanie", "uzytkownik"]
        ordering = ["uzytkownik"]
        verbose_name = "Głos komisji"
        verbose_name_plural = "Głosy komisji"


class KomisjaWniosek(models.Model):
    TYP_CHOICES = [("wniosek", "Wniosek"), ("zapytanie", "Zapytanie"), ("postulat", "Postulat")]
    komisja = models.ForeignKey(Komisja, on_delete=models.CASCADE, related_name="wnioski")
    sesja = models.ForeignKey(KomisjaSesja, on_delete=models.SET_NULL, null=True, blank=True)
    punkt_obrad = models.ForeignKey(KomisjaPunktObrad, on_delete=models.SET_NULL, null=True, blank=True)
    autor = models.ForeignKey(Uzytkownik, on_delete=models.PROTECT, related_name="komisja_wnioski")
    typ = models.CharField(max_length=20, choices=TYP_CHOICES, default="wniosek")
    tresc = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    wyslany_do_rady = models.BooleanField(default=False)
    data_wyslania = models.DateTimeField(null=True, blank=True)
    zatwierdzony_przez_prezydium = models.BooleanField(default=False)
    data_zatwierdzenia = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "Wniosek komisji"
        verbose_name_plural = "Wnioski komisji"

    def __str__(self):
        return f"{self.get_typ_display()} ({self.komisja})"

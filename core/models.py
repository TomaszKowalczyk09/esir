from django.db import models
from accounts.models import Uzytkownik
from django.utils import timezone


class Sesja(models.Model):
    nazwa = models.CharField(max_length=200)
    data = models.DateTimeField(default=timezone.now)
    aktywna = models.BooleanField(default=True)
    jest_usunieta = models.BooleanField(default=False)  # NOWE POLE

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



class PunktObrad(models.Model):
    sesja = models.ForeignKey(Sesja, on_delete=models.CASCADE, related_name='punkty')
    numer = models.IntegerField()
    tytul = models.CharField(max_length=300)
    opis = models.TextField(blank=True)
    aktywny = models.BooleanField(default=False)  # ważne

    class Meta:
        ordering = ['numer']



    def __str__(self):
        return f"{self.numer}. {self.tytul}"


class Glosowanie(models.Model):
    punkt_obrad = models.OneToOneField(PunktObrad, on_delete=models.CASCADE, related_name='glosowanie')
    nazwa = models.CharField(max_length=200)
    otwarte = models.BooleanField(default=False)
    utworzone = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nazwa


class Glos(models.Model):
    glosowanie = models.ForeignKey(Glosowanie, on_delete=models.CASCADE)
    uzytkownik = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE)
    glos = models.CharField(max_length=10,
                            choices=[('za', 'Za'), ('przeciw', 'Przeciw'), ('wstrzymuje', 'Wstrzymuję się')])

    class Meta:
        unique_together = ['glosowanie', 'uzytkownik']
        ordering = ['uzytkownik']


class Wniosek(models.Model):
    punkt_obrad = models.ForeignKey(PunktObrad, on_delete=models.CASCADE, related_name='wnioski')
    radny = models.ForeignKey(Uzytkownik, on_delete=models.CASCADE)
    tresc = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    zatwierdzony = models.BooleanField(default=False)

    def __str__(self):
        return f"Wniosek {self.radny} - {self.tresc[:50]}"

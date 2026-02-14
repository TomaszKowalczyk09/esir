from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Uzytkownik(AbstractUser):
    ROLA_WYBOR = [
        ('radny', 'Radny'),
        ('prezydium', 'Prezydium'),
        ('administrator', 'Administrator'),
    ]
    rola = models.CharField(max_length=15, choices=ROLA_WYBOR, default='radny')
    imie = models.CharField(max_length=50)
    nazwisko = models.CharField(max_length=50)
    must_change_password = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Synchronizuje rolę biznesową z uprawnieniami Django.

        Założenie: rola 'administrator' ma automatyczny dostęp do /admin/
        na podstawie własnych danych logowania.
        """
        if self.rola == "administrator":
            # dostęp do panelu admina
            self.is_staff = True
            # pełne uprawnienia w panelu (bez konieczności ręcznego nadawania permissions)
            self.is_superuser = True
        else:
            # pozostałe role nie mają automatycznie uprawnień administracyjnych
            self.is_superuser = False
            # jeśli chcesz, aby np. 'prezydium' też miało dostęp, zmień warunek powyżej
            self.is_staff = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.imie} {self.nazwisko} ({self.rola})"

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

    
    opis = models.TextField(blank=True, default="")

    def save(self, *args, **kwargs):
        """Synchronizuje rolę biznesową z uprawnieniami Django.

        Założenie: rola 'administrator' ma automatyczny dostęp do /admin/
        na podstawie własnych danych logowania.
        """
        if self.rola == "administrator":
            
            self.is_staff = True
            
            self.is_superuser = True
        else:
            
            self.is_superuser = False
            
            self.is_staff = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.imie} {self.nazwisko} ({self.rola})"

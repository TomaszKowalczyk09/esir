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

    def __str__(self):
        return f"{self.imie} {self.nazwisko} ({self.rola})"

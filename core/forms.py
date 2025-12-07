from django import forms
from .models import Sesja, PunktObrad, Glosowanie

class SesjaForm(forms.ModelForm):
    class Meta:
        model = Sesja
        fields = ['nazwa', 'data', 'aktywna']

class PunktObradForm(forms.ModelForm):
    class Meta:
        model = PunktObrad
        fields = ['sesja', 'numer', 'tytul', 'opis']

class GlosowanieForm(forms.ModelForm):
    class Meta:
        model = Glosowanie
        fields = ['punkt_obrad', 'nazwa', 'otwarte']


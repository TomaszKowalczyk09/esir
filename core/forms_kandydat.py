from django import forms
from .models import Kandydat

class KandydatForm(forms.ModelForm):
    class Meta:
        model = Kandydat
        fields = ["imie", "nazwisko", "opis"]
        widgets = {
            "imie": forms.TextInput(attrs={"class": "form-control"}),
            "nazwisko": forms.TextInput(attrs={"class": "form-control"}),
            "opis": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
        labels = {
            "imie": "Imię",
            "nazwisko": "Nazwisko",
            "opis": "Opis (opcjonalnie)",
        }

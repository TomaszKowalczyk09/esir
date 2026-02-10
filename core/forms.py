from django import forms
from .models import Sesja, PunktObrad, Glosowanie, Wniosek


class SesjaCreateForm(forms.ModelForm):
    """Prosty formularz tworzenia / edycji sesji dla prezydium."""
    class Meta:
        model = Sesja
        fields = ["nazwa", "data", "aktywna"]
        widgets = {
            "nazwa": forms.TextInput(attrs={"class": "form-control"}),
            "data": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "aktywna": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "nazwa": "Nazwa sesji",
            "data": "Data i godzina",
            "aktywna": "Sesja aktywna",
        }


class PunktForm(forms.ModelForm):
    """Dodawanie / edycja punktu obrad w ramach wybranej sesji."""
    class Meta:
        model = PunktObrad
        fields = ["numer", "tytul", "opis"]
        widgets = {
            "numer": forms.NumberInput(attrs={"class": "form-control"}),
            "tytul": forms.TextInput(attrs={"class": "form-control"}),
            "opis": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "numer": "Numer punktu",
            "tytul": "Tytuł",
            "opis": "Opis (opcjonalnie)",
        }


class GlosowanieForm(forms.ModelForm):
    """Tworzenie głosowania dla wybranego punktu obrad.

    Nazwa głosowania jest automatycznie ustawiana na podstawie tytułu punktu obrad.
    """
    class Meta:
        model = Glosowanie
        fields = ["jawnosc", "wiekszosc", "liczba_uprawnionych"]
        widgets = {
            "jawnosc": forms.Select(attrs={"class": "form-select"}),
            "wiekszosc": forms.Select(attrs={"class": "form-select"}),
            "liczba_uprawnionych": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }
        labels = {
            "jawnosc": "Jawność",
            "wiekszosc": "Rodzaj większości",
            "liczba_uprawnionych": "Liczba uprawnionych (opcjonalnie)",
        }


class WniosekForm(forms.ModelForm):
    """Formularz wniosku radnego (jeśli będziesz chciał go użyć w panelu)."""
    class Meta:
        model = Wniosek
        fields = ["tresc"]
        widgets = {
            "tresc": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "tresc": "Treść wniosku",
        }

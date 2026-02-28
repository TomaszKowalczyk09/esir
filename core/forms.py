from django import forms
from .models import Sesja, PunktObrad, Glosowanie, Wniosek, Komisja, KomisjaSesja, KomisjaPunktObrad, KomisjaWniosek


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
        fields = ["tytul", "opis"]
        widgets = {
            "tytul": forms.TextInput(attrs={"class": "form-control"}),
            "opis": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "tytul": "Tytuł",
            "opis": "Opis (opcjonalnie)",
        }


class GlosowanieForm(forms.ModelForm):
    """Tworzenie głosowania dla wybranego punktu obrad.

    Nazwa głosowania jest automatycznie ustawiana na podstawie tytułu punktu obrad.
    """
    class Meta:
        model = Glosowanie
        fields = ["typ", "jawnosc", "wiekszosc", "liczba_uprawnionych"]
        widgets = {
            "typ": forms.Select(attrs={"class": "form-select"}),
            "jawnosc": forms.Select(attrs={"class": "form-select"}),
            "wiekszosc": forms.Select(attrs={"class": "form-select"}),
            "liczba_uprawnionych": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }
        labels = {
            "typ": "Typ głosowania",
            "jawnosc": "Jawność",
            "wiekszosc": "Rodzaj większości",
            "liczba_uprawnionych": "Liczba uprawnionych (opcjonalnie)",
        }


class WniosekForm(forms.ModelForm):
    """Formularz wniosku radnego (jeśli będziesz chciał go użyć w panelu)."""
    class Meta:
        model = Wniosek
        fields = ["typ", "tresc"]
        widgets = {
            "typ": forms.Select(attrs={"class": "form-select"}),
            "tresc": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "typ": "Rodzaj",
            "tresc": "Treść",
        }


class KomisjaForm(forms.ModelForm):
    class Meta:
        model = Komisja
        fields = ["nazwa", "opis", "przewodniczacy", "czlonkowie", "aktywna"]
        widgets = {
            "czlonkowie": forms.CheckboxSelectMultiple,
        }


class KomisjaSesjaForm(forms.ModelForm):
    class Meta:
        model = KomisjaSesja
        fields = ["nazwa", "data", "aktywna"]


class KomisjaPunktForm(forms.ModelForm):
    class Meta:
        model = KomisjaPunktObrad
        fields = ["numer", "tytul", "opis"]


class KomisjaWniosekForm(forms.ModelForm):
    class Meta:
        model = KomisjaWniosek
        fields = ["typ", "tresc"]
        widgets = {
            "tresc": forms.Textarea(attrs={"rows": 4}),
        }

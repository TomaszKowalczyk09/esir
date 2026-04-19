from django import forms
from .models import (
    Sesja,
    PunktObrad,
    PodpunktObrad,
    Glosowanie,
    Wniosek,
    Komisja,
    KomisjaSesja,
    KomisjaPunktObrad,
    KomisjaPodpunktObrad,
    KomisjaWniosek,
    KomisjaGlosowanie,
)


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
            "tytul": forms.TextInput(attrs={"class": "form-control", "placeholder": "Np. Budżet, inwestycje, transport"}),
            "opis": forms.Textarea(
                attrs={
                    "class": "form-control punkt-opis-editor",
                    "rows": 5,
                    "placeholder": "Możesz użyć formatowania: **pogrubienie**, *kursywa*, __podkreślenie__, - lista",
                }
            ),
        }
        labels = {
            "tytul": "Tytuł",
            "opis": "Opis (opcjonalnie)",
        }


class PodpunktForm(forms.ModelForm):
    class Meta:
        model = PodpunktObrad
        fields = ["tytul", "opis"]
        widgets = {
            "tytul": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tytuł podpunktu"}),
            "opis": forms.Textarea(
                attrs={
                    "class": "form-control punkt-opis-editor",
                    "rows": 3,
                    "placeholder": "Opis podpunktu (opcjonalnie)",
                }
            ),
        }
        labels = {
            "tytul": "Tytuł podpunktu",
            "opis": "Opis podpunktu",
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
        fields = ["tytul", "opis"]
        widgets = {
            "tytul": forms.TextInput(attrs={"class": "form-control", "placeholder": "Np. Budżet, transport, inwestycje"}),
            "opis": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Krótki opis punktu obrad"}),
        }


class KomisjaPodpunktForm(forms.ModelForm):
    class Meta:
        model = KomisjaPodpunktObrad
        fields = ["tytul", "opis"]
        widgets = {
            "tytul": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tytuł podpunktu"}),
            "opis": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Krótki opis podpunktu"}),
        }


class KomisjaWniosekForm(forms.ModelForm):
    class Meta:
        model = KomisjaWniosek
        fields = ["typ", "tresc"]
        widgets = {
            "tresc": forms.Textarea(attrs={"rows": 4}),
        }


class KomisjaGlosowanieForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nazwa może być pusta - widok ustawi domyślnie tytuł punktu/podpunktu.
        self.fields["nazwa"].required = False

    class Meta:
        model = KomisjaGlosowanie
        fields = ["nazwa", "jawnosc", "wiekszosc", "liczba_uprawnionych"]
        widgets = {
            "nazwa": forms.TextInput(attrs={"class": "form-control"}),
            "jawnosc": forms.Select(attrs={"class": "form-select"}),
            "wiekszosc": forms.Select(attrs={"class": "form-select"}),
            "liczba_uprawnionych": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

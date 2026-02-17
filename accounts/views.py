from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # jeśli trzeba, kierujemy od razu do zmiany hasła
            if getattr(user, "must_change_password", False):
                return redirect("change_password_first")
            return redirect("panel")
        else:
            messages.error(request, "Błędny login lub hasło.")
    return render(request, "core/login.html")


def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def change_password_first(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            request.user.must_change_password = False
            request.user.save()
            messages.success(request, "Hasło zostało zmienione.")
            return redirect("panel")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(
        request,
        "core/change_password_first.html",
        {
            "form": form,
            "force_public_layout": True,  # bez menu przy wymuszonej zmianie hasła
        },
    )


class ProfilForm(forms.ModelForm):
    class Meta:
        from .models import Uzytkownik

        model = Uzytkownik
        fields = ["opis"]
        widgets = {
            "opis": forms.Textarea(attrs={"rows": 4, "placeholder": "Krótki opis..."}),
        }


@login_required
def profil_edytuj(request):
    if request.method == "POST":
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, "Profil został zaktualizowany.")
                return redirect("profil_edytuj")
            except Exception:
                logger.exception("Błąd zapisu profilu użytkownika id=%s", getattr(request.user, "id", None))
                form.add_error(None, "Nie udało się zapisać profilu. Spróbuj ponownie lub skontaktuj się z administratorem.")
    else:
        form = ProfilForm(instance=request.user)

    return render(request, "accounts/profil_edytuj.html", {"form": form})

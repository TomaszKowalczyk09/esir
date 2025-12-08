from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib import messages


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

    return render(request, "core/change_password_first.html", {"form": form})

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('panel')
        else:
            messages.error(request, 'Błędny login lub hasło')
    return render(request, 'core/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')


from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib import messages

def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if getattr(user, "must_change_password", False):
                return redirect("change_password_first")
            return redirect("panel")
        else:
            messages.error(request, "Błędny login lub hasło")
    return render(request, "core/login.html")

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

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
        # JEŚLI NIE JEST VALID: po prostu wpadamy w else niżej i wyrenderujemy form z błędami
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "core/change_password_first.html", {"form": form})


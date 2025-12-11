from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Sesja, PunktObrad, Glosowanie, Glos, Wniosek
from django.db.models import Count
from django.forms import ModelForm, Textarea
from django import forms


class WniosekForm(ModelForm):
    class Meta:
        model = Wniosek
        fields = ['tresc']
        widgets = {'tresc': Textarea(attrs={'rows': 3})}


@login_required
def panel(request):
    if request.user.rola == 'prezydium':
        return prezidium_panel(request)
    return radny_panel(request)


from .forms import SesjaForm, PunktObradForm, GlosowanieForm
from django.contrib import messages
from django.views.decorators.http import require_POST


# core/views.py

@login_required
def prezidium_panel(request):
    if request.user.rola != 'prezydium':
        return redirect('radny')

    sesja_aktywna = Sesja.objects.filter(aktywna=True, jest_usunieta=False) \
        .prefetch_related('punkty__glosowanie') \
        .first()

    glosowania = []
    if sesja_aktywna:
        glosowania = Glosowanie.objects.filter(
            punkt_obrad__sesja=sesja_aktywna
        ).select_related('punkt_obrad')

    context = {
        'sesja_aktywna': sesja_aktywna,
        'glosowania': glosowania,
    }
    return render(request, 'core/prezidium.html', context)


@require_POST
@login_required
def usun_sesje(request, sesja_id):
    if request.user.rola != 'prezydium':
        return redirect('radny')
    sesja = get_object_or_404(Sesja, id=sesja_id)
    sesja.delete()  # kaskadowo usunie punkty, głosowania i głosy
    messages.success(request, 'Sesja została usunięta.')
    return redirect('prezidium')



def radny_panel(request):
    aktywna_sesja = Sesja.objects.filter(aktywna=True).first()
    if aktywna_sesja:
        glosowania = Glosowanie.objects.filter(
            punkt_obrad__sesja=aktywna_sesja,
            otwarte=True
        ).select_related('punkt_obrad')
    else:
        glosowania = []
    return render(request, 'core/radny.html', {'glosowania': glosowania})


@login_required
def toggle_glosowanie(request, glosowanie_id):
    if request.user.rola != 'prezydium':
        return JsonResponse({'error': 'Brak uprawnień'})

    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    glosowanie.otwarte = not glosowanie.otwarte
    glosowanie.save()
    return JsonResponse({'otwarte': glosowanie.otwarte})


from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Glosowanie, Glos

@require_http_methods(["POST"])
@login_required
def oddaj_glos(request, glosowanie_id):
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)

    if not glosowanie.otwarte:
        return JsonResponse({'error': 'Głosowanie zamknięte'})

    wartosc = request.POST.get('glos')
    print("POST:", request.POST, "wartosc glosu:", wartosc)

    # JEŚLI z jakiegoś powodu dalej None – nie zapisujemy, ale też nie wywalamy bazy
    if wartosc not in ['za', 'przeciw', 'wstrzymuje']:
        return JsonResponse({'error': 'Nieprawidłowa wartość głosu'})

    glos, created = Glos.objects.get_or_create(
        glosowanie=glosowanie,
        uzytkownik=request.user,
        defaults={'glos': wartosc}
    )

    if not created:
        return JsonResponse({'error': 'Już oddałeś głos w tym głosowaniu'})

    return JsonResponse({'success': True})



def api_wyniki(request, glosowanie_id):
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    wyniki = Glos.objects.filter(glosowanie=glosowanie).values(
        'glos'
    ).annotate(
        count=Count('glos')
    )

    dane = {'za': 0, 'przeciw': 0, 'wstrzymuje': 0}
    for wynik in wyniki:
        dane[wynik['glos']] = wynik['count']

    return JsonResponse(dane)


def wyniki_publiczne(request, sesja_id=None):
    sesja = Sesja.objects.filter(aktywna=True).first()
    if sesja:
        punkty = sesja.punkty.select_related('glosowanie').prefetch_related('glosowanie__glos_set')
    else:
        punkty = []
    return render(request, 'core/wyniki.html', {'punkty': punkty})

from django.db.models import Count

def punkt_ekran(request, punkt_id):
    punkt = get_object_or_404(PunktObrad, id=punkt_id)
    glosowanie = getattr(punkt, 'glosowanie', None)
    wyniki = None
    if glosowanie:
        agregaty = Glos.objects.filter(glosowanie=glosowanie).values(
            'glos'
        ).annotate(count=Count('glos'))
        wyniki = {'za': 0, 'przeciw': 0, 'wstrzymuje': 0}
        for w in agregaty:
            wyniki[w['glos']] = w['count']
    return render(request, 'core/punkt_ekran.html', {
        'punkt': punkt,
        'glosowanie': glosowanie,
        'wyniki': wyniki,
    })

from django.http import JsonResponse

from django.db.models import Count

from django.db.models import Count

def api_aktywny_punkt(request, sesja_id):
    sesja = get_object_or_404(Sesja, id=sesja_id)
    punkt = sesja.punkty.filter(aktywny=True).select_related('glosowanie').first()
    if not punkt:
        return JsonResponse({'aktywny': False})

    glosowanie = getattr(punkt, 'glosowanie', None)
    dane = {
        'aktywny': True,
        'punkt_id': punkt.id,
        'numer': punkt.numer,
        'tytul': punkt.tytul,
        'opis': punkt.opis,
        'glosowanie_id': glosowanie.id if glosowanie else None,
        'glosowanie_nazwa': glosowanie.nazwa if glosowanie else None,
        'glosowanie_otwarte': glosowanie.otwarte if glosowanie else False,
        'za': 0,
        'przeciw': 0,
        'wstrzymuje': 0,
    }

    if glosowanie:
        wyniki = Glos.objects.filter(glosowanie=glosowanie).values('glos').annotate(
            count=Count('glos')
        )
        for w in wyniki:
            dane[w['glos']] = w['count']

    return JsonResponse(dane)


def sesja_ekran(request, sesja_id):
    sesja = get_object_or_404(Sesja, id=sesja_id)
    return render(request, 'core/sesja_ekran.html', {'sesja': sesja})

from django.views.decorators.http import require_POST

@require_POST
@login_required
def ustaw_sesje_aktywna(request, sesja_id):
    if request.user.rola != 'prezydium':
        return redirect('radny')
    sesja = get_object_or_404(Sesja, id=sesja_id)
    sesja.ustaw_aktywna()
    return redirect('prezidium')

from django.views.decorators.http import require_POST


# core/views.py

@require_POST
@login_required
def ustaw_punkt_aktywny(request, punkt_id):
    if request.user.rola != 'prezydium':
        return redirect('radny')

    punkt = get_object_or_404(PunktObrad, id=punkt_id)
    PunktObrad.objects.filter(sesja=punkt.sesja).update(aktywny=False)
    punkt.aktywny = True
    punkt.save()

    # Wróć do poprzedniej strony zamiast na prezidium
    return redirect(request.META.get('HTTP_REFERER', 'porzadek_obrad_prezidium'))


from django.contrib.auth.decorators import login_required
from .models import Sesja, PunktObrad

@login_required
def porzadek_obrad(request):
    # aktualna aktywna sesja – tę pokazujemy radnym
    sesja = Sesja.objects.filter(aktywna=True, jest_usunieta=False).prefetch_related('punkty').first()
    return render(request, 'core/porzadek_obrad.html', {'sesja': sesja})

@login_required
def porzadek_obrad_prezidium(request):
    if request.user.rola != 'prezydium':
        return redirect('porzadek_obrad')

    # obsługa formularzy
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'sesja':
            form = SesjaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Sesja została utworzona.')
        elif form_type == 'punkt':
            form = PunktObradForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Punkt obrad został dodany.')
        elif form_type == 'glosowanie':
            form = GlosowanieForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Głosowanie zostało utworzone.')
        return redirect('porzadek_obrad_prezidium')

    sesje = Sesja.objects.filter(jest_usunieta=False).prefetch_related('punkty__glosowanie')
    context = {
        'sesje': sesje,
        'sesja_form': SesjaForm(),
        'punkt_form': PunktObradForm(),
        'glosowanie_form': GlosowanieForm(),
    }
    return render(request, 'core/porzadek_obrad_prezidium.html', context)


from django.http import JsonResponse


def api_lista_glosow(request, glosowanie_id):
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    glosy = Glos.objects.filter(glosowanie=glosowanie).select_related('uzytkownik').values(
        'uzytkownik__first_name',
        'uzytkownik__last_name',
        'glos'
    )

    lista = []
    for glos in glosy:
        lista.append({
            'imie': glos['uzytkownik__first_name'],
            'nazwisko': glos['uzytkownik__last_name'],
            'glos': glos['glos']
        })

    return JsonResponse({'glosy': lista})

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sesja


def _czy_prezydium(user):
    return user.is_authenticated and getattr(user, "rola", "") == "prezydium"


@login_required
def zamknij_sesje(request, sesja_id):
    if not _czy_prezydium(request.user):
        messages.error(request, "Nie masz uprawnień do zamykania sesji.")
        return redirect("panel")

    sesja = get_object_or_404(Sesja, pk=sesja_id, jest_usunieta=False)
    sesja.zamknij()
    messages.success(request, "Sesja została zamknięta.")
    return redirect("prezidium_panel")  # u Ciebie to prezidium_panel()


@login_required
def usun_sesje(request, sesja_id):
    if not _czy_prezydium(request.user):
        messages.error(request, "Nie masz uprawnień do usuwania sesji.")
        return redirect("panel")

    sesja = get_object_or_404(Sesja, pk=sesja_id, jest_usunieta=False)

    if request.method == "POST":
        sesja.usun()
        messages.success(request, "Sesja została usunięta z listy.")
        return redirect("prezidium_panel")

    return render(request, "core/potwierdz_usuniecie_sesji.html", {"sesja": sesja})

from django.utils import timezone
@login_required
def nadchodzace_sesje(request):
    teraz = timezone.now()
    sesje = (Sesja.objects
             .filter(opublikowana=True, data__gte=teraz)
             .prefetch_related('punkty')
             .order_by('data'))
    return render(request, 'core/nadchodzace_sesje.html', {'sesje': sesje})
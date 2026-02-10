from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db.models import Count, Q
from django.utils import timezone

from .models import Sesja, PunktObrad, Glosowanie, Glos, Wniosek
from .forms import SesjaCreateForm, PunktForm, GlosowanieForm, WniosekForm
from accounts.models import Uzytkownik


# --------------------------------------------------
# Wspólny panel startowy
# --------------------------------------------------

@login_required
def panel(request):
    """
    Po zalogowaniu kieruje:
    - prezydium -> dashboard prezydium
    - radny -> panel radnego z listą głosowań
    """
    if request.user.rola == "prezydium":
        return redirect("prezydium_dashboard")
    return redirect("radny")


# --------------------------------------------------
# Widoki PREZYDIUM
# --------------------------------------------------

@login_required
def prezydium_dashboard(request):
    """
    Prosty dashboard: pokazuje najbliższą sesję, liczbę punktów i otwartych głosowań.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    najblizsza = (
        Sesja.objects.order_by("data")
        .prefetch_related("punkty__glosowanie")
        .first()
    )

    liczba_sesji = Sesja.objects.count()
    liczba_punktow = PunktObrad.objects.count()
    liczba_glosowan_otwartych = Glosowanie.objects.filter(otwarte=True).count()

    context = {
        "najblizsza": najblizsza,
        "liczba_sesji": liczba_sesji,
        "liczba_punktow": liczba_punktow,
        "liczba_glosowan_otwartych": liczba_glosowan_otwartych,
    }
    return render(request, "core/prezydium_dashboard.html", context)


@login_required
def prezydium_sesje(request):
    """
    Lista wszystkich sesji z podstawowymi akcjami (bez szczegółowej edycji).
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesje = Sesja.objects.all().order_by("-data")
    return render(request, "core/prezydium_sesje.html", {"sesje": sesje})


@login_required
def sesja_nowa(request):
    """
    Kreator tworzenia nowej sesji – po zapisaniu przekierowuje do edycji sesji.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    if request.method == "POST":
        form = SesjaCreateForm(request.POST)
        if form.is_valid():
            sesja = form.save()
            messages.success(request, "Sesja została utworzona.")
            return redirect("sesja_edytuj", sesja_id=sesja.id)
    else:
        form = SesjaCreateForm()

    return render(request, "core/sesja_nowa.html", {"form": form})


@login_required
def sesja_edytuj(request, sesja_id):
    """
    Jeden ekran do zarządzania porządkiem obrad:
    - dodawanie punktów,
    - dodawanie głosowań do punktów.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = get_object_or_404(Sesja, id=sesja_id)

    if request.method == "POST":
        if "dodaj_punkt" in request.POST:
            punkt_form = PunktForm(request.POST)
            glosowanie_form = GlosowanieForm()
            if punkt_form.is_valid():
                punkt = punkt_form.save(commit=False)
                punkt.sesja = sesja
                punkt.save()
                messages.success(request, "Punkt obrad został dodany.")
                return redirect("sesja_edytuj", sesja_id=sesja.id)

        elif "dodaj_glosowanie" in request.POST:
            punkt_form = PunktForm()
            glosowanie_form = GlosowanieForm(request.POST)
            if glosowanie_form.is_valid():
                punkt = get_object_or_404(
                    PunktObrad, id=request.POST.get("punkt_id"), sesja=sesja
                )
                gl = glosowanie_form.save(commit=False)
                gl.punkt_obrad = punkt
                gl.nazwa = punkt.tytul
                gl.save()
                messages.success(request, "Głosowanie zostało dodane.")
                return redirect("sesja_edytuj", sesja_id=sesja.id)
    else:
        punkt_form = PunktForm()
        glosowanie_form = GlosowanieForm()

    punkty = sesja.punkty.select_related("glosowanie").all()

    context = {
        "sesja": sesja,
        "punkty": punkty,
        "punkt_form": punkt_form,
        "glosowanie_form": glosowanie_form,
    }
    return render(request, "core/sesja_edytuj.html", context)


@login_required
@require_POST
def ustaw_sesje_aktywna(request, sesja_id):
    """
    Ustawia daną sesję jako aktywną, inne sesje dezaktywuje.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = get_object_or_404(Sesja, id=sesja_id)
    Sesja.objects.update(aktywna=False)
    sesja.aktywna = True
    sesja.save()
    messages.success(request, "Sesja została ustawiona jako aktywna.")
    return redirect("prezydium_sesje")


@login_required
@require_POST
def dezaktywuj_sesje(request, sesja_id):
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = get_object_or_404(Sesja, id=sesja_id)
    sesja.aktywna = False
    sesja.save()
    messages.success(request, "Sesja została dezaktywowana.")
    return redirect("prezydium_sesje")


@login_required
@require_POST
def usun_sesje(request, sesja_id):
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = get_object_or_404(Sesja, id=sesja_id)
    sesja.delete()
    messages.success(request, "Sesja została usunięta.")
    return redirect("prezydium_sesje")


@login_required
def porzadek_obrad_prezidium(request):
    """
    Widok porządku obrad dla prezydium – pracuje zawsze na aktywnej sesji.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = Sesja.objects.filter(aktywna=True).prefetch_related("punkty").first()

    if request.method == "POST" and sesja:
        form = PunktForm(request.POST)
        if form.is_valid():
            punkt = form.save(commit=False)
            punkt.sesja = sesja
            punkt.save()
            messages.success(request, "Punkt obrad został dodany.")
            return redirect("porzadek_obrad_prezidium")
    else:
        form = PunktForm()

    return render(
        request,
        "core/porzadek_obrad_prezidium.html",
        {"sesja": sesja, "punkt_form": form},
    )


@login_required
def prezidium_panel(request):
    """
    Dotychczasowy widok głosowań prezydium – lista sesji, punktów i głosowań + otwieranie/zamykanie.
    Zostaje jako zakładka „Głosowania”.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesje = Sesja.objects.all().prefetch_related("punkty__glosowanie")
    return render(request, "core/prezidium.html", {"sesje": sesje})


@login_required
def nadchodzace_sesje_prezidium(request):
    """
    Prosta lista sesji (np. aktywnych lub wszystkich) – wykorzystasz w menu 'Nadchodzące sesje'.
    Na razie pokazuje wszystkie sesje posortowane rosnąco po dacie.
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesje = Sesja.objects.all().order_by("data")
    return render(request, "core/nadchodzace_sesje_prezidium.html", {"sesje": sesje})


# --------------------------------------------------
# Widoki RADNEGO
# --------------------------------------------------

@login_required
def radny_panel(request):
    """
    Panel radnego – alias na radny (dla spójności z panelem).
    """
    return redirect("radny")


@login_required
def radny(request):
    """
    Główna strona radnego:
    - informacje o aktywnej sesji,
    - porządek obrad (lista punktów),
    - lista otwartych głosowań.
    """
    if request.user.rola != "radny":
        return redirect("prezydium_dashboard")

    aktywna_sesja = Sesja.objects.filter(aktywna=True).first()

    glosowania = []
    punkty = []
    if aktywna_sesja:
        punkty = aktywna_sesja.punkty.select_related("glosowanie").order_by("numer")
        glosowania = (
            Glosowanie.objects.filter(
                punkt_obrad__sesja=aktywna_sesja,
                otwarte=True,
            )
            .select_related("punkt_obrad")
            .order_by("punkt_obrad__numer")
        )

    context = {
        "sesja": aktywna_sesja,
        "punkty": punkty,
        "glosowania": glosowania,
    }
    return render(request, "core/radny.html", context)


# --------------------------------------------------
# Operacje na głosowaniach
# --------------------------------------------------

@login_required
def toggle_glosowanie(request, glosowanie_id):
    """
    Otwieranie / zamykanie głosowania – tylko prezydium.
    """
    if request.user.rola != "prezydium":
        return JsonResponse({"error": "Brak uprawnień"})

    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    glosowanie.otwarte = not glosowanie.otwarte
    glosowanie.save()
    return JsonResponse({"otwarte": glosowanie.otwarte})


@require_http_methods(["POST"])
@login_required
def oddaj_glos(request, glosowanie_id):
    """
    Radny oddaje głos – blokada wielokrotnego głosowania.

    Zwraca JSON dla żądań AJAX, a dla zwykłych POST-ów zwraca czytelny komunikat HTML.
    """
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)

    def is_ajax(req):
        return req.headers.get("x-requested-with") == "XMLHttpRequest"

    if not glosowanie.otwarte:
        if is_ajax(request):
            return JsonResponse({"error": "Głosowanie zamknięte"})
        messages.error(request, "Głosowanie jest zamknięte.")
        return redirect("radny")

    wartosc = request.POST.get("glos")
    if wartosc not in ["za", "przeciw", "wstrzymuje"]:
        if is_ajax(request):
            return JsonResponse({"error": "Nieprawidłowa wartość głosu"})
        messages.error(request, "Nieprawidłowa wartość głosu.")
        return redirect("radny")

    glos, created = Glos.objects.get_or_create(
        glosowanie=glosowanie,
        uzytkownik=request.user,
        defaults={"glos": wartosc},
    )

    if not created:
        if is_ajax(request):
            return JsonResponse({"error": "Już oddałeś głos w tym głosowaniu"})
        messages.warning(request, "Już oddałeś głos w tym głosowaniu.")
        return redirect("radny")

    if is_ajax(request):
        return JsonResponse({"success": True})

    messages.success(request, "Głos został zapisany.")
    return redirect("radny")


def api_wyniki(request, glosowanie_id):
    """
    API z podsumowaniem wyników głosowania (Za / Przeciw / Wstrzymuję).

    Dla głosowań tajnych: w trakcie (otwarte=True) zwracamy zagregowaną informację bez rozbicia.
    """
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)

    # Tajne: w trakcie nie ujawniamy wyników szczegółowych
    if (glosowanie.jawnosc == "tajne" and glosowanie.otwarte):
        total = Glos.objects.filter(glosowanie=glosowanie).count()
        return JsonResponse({
            "tajne": True,
            "otwarte": True,
            "oddano": total,
        })

    wyniki = (
        Glos.objects.filter(glosowanie=glosowanie)
        .values("glos")
        .annotate(count=Count("glos"))
    )

    dane = {"za": 0, "przeciw": 0, "wstrzymuje": 0}
    for wynik in wyniki:
        dane[wynik["glos"]] = wynik["count"]

    podsumowanie = glosowanie.wynik_podsumowanie()

    return JsonResponse({
        **dane,
        "tajne": glosowanie.jawnosc == "tajne",
        "otwarte": glosowanie.otwarte,
        "wiekszosc": glosowanie.wiekszosc,
        "przeszedl": podsumowanie["przeszedl"],
        "prog": podsumowanie["prog"],
    })


@require_GET
def api_lista_glosow_jawne(request, glosowanie_id):
    """API: lista głosów imiennych dla głosowania jawnego.

    Zwraca wszystkich uprawnionych do głosowania (radni + prezydium)
    w kolejności: nazwisko, imię wraz z informacją jak zagłosowali:
    za/przeciw/wstrzymuje lub null (brak).

    Dla głosowań tajnych zwraca 403.
    """
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    if glosowanie.jawnosc != "jawne":
        return JsonResponse({"error": "Głosowanie nie jest jawne"}, status=403)

    uprawnieni = Uzytkownik.objects.filter(rola__in=["radny", "prezydium"]).order_by("nazwisko", "imie")
    glosy = {
        g.uzytkownik_id: g.glos
        for g in Glos.objects.filter(glosowanie=glosowanie).select_related("uzytkownik")
    }

    items = []
    for r in uprawnieni:
        items.append({
            "id": r.id,
            "imie": r.imie,
            "nazwisko": r.nazwisko,
            "rola": r.rola,
            "glos": glosy.get(r.id),
        })

    return JsonResponse({
        "jawne": True,
        "glosowanie_id": glosowanie.id,
        "items": items,
    })


# --------------------------------------------------
# Widok wyników publicznych
# --------------------------------------------------

def wyniki_publiczne(request, sesja_id=None):
    """
    Publiczny ekran wyników – pokazuje wszystkie głosowania w aktywnej sesji.
    """
    sesja = Sesja.objects.filter(aktywna=True).first()
    if sesja:
        punkty = sesja.punkty.select_related("glosowanie").prefetch_related(
            "glosowanie__glos_set"
        )
    else:
        punkty = []

    return render(request, "core/wyniki.html", {"punkty": punkty})


@login_required
def sesja_ekran(request, sesja_id):
    """
    Publiczny ekran sesji wyświetlany na rzutniku w sali obrad.
    """
    sesja = get_object_or_404(Sesja, id=sesja_id)
    return render(request, "core/sesja_ekran.html", {"sesja": sesja})


@require_GET
def api_aktywny_punkt(request, sesja_id):
    """
    Zwraca dane aktywnego punktu i ewentualnego głosowania do ekranu sesji.
    Zakładamy, że w danej chwili max 1 punkt jest „aktywny”.
    """
    sesja = get_object_or_404(Sesja, id=sesja_id)

    punkt = (
        sesja.punkty.filter(Q(aktywny=True) | Q())
        .select_related("glosowanie")
        .order_by("numer")
        .first()
    )

    if not punkt:
        return JsonResponse({"aktywny": False})

    glosowanie = getattr(punkt, "glosowanie", None)

    data = {
        "aktywny": True,
        "numer": punkt.numer,
        "tytul": punkt.tytul,
        "podtytul": "",
        "opis": punkt.opis or "",
        "glosowanie_id": glosowanie.id if glosowanie else None,
        "glosowanie_nazwa": glosowanie.nazwa if glosowanie else "",
        "za": 0,
        "przeciw": 0,
        "wstrzymuje": 0,
    }

    if glosowanie:
        wyniki = (
            Glos.objects.filter(glosowanie=glosowanie)
            .values("glos")
            .annotate(count=Count("glos"))
        )
        for w in wyniki:
            if w["glos"] == "za":
                data["za"] = w["count"]
            elif w["glos"] == "przeciw":
                data["przeciw"] = w["count"]
            elif w["glos"] == "wstrzymuje":
                data["wstrzymuje"] = w["count"]

    return JsonResponse(data)


@login_required
@require_POST
def ustaw_punkt_aktywny(request, punkt_id):
    if request.user.rola != "prezydium":
        return redirect("radny")

    punkt = get_object_or_404(PunktObrad, id=punkt_id)
    PunktObrad.objects.filter(sesja=punkt.sesja).update(aktywny=False)
    punkt.aktywny = True
    punkt.save()
    return redirect("prezydium_agenda")


@login_required
def prezydium_agenda(request):
    """
    Prosty ekran sterowania sesją dla prezydium:
    - pokazuje punkty aktywnej sesji,
    - pozwala ustawić aktywny punkt,
    - pokazuje stan głosowania (otwarte/zamknięte).
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = Sesja.objects.filter(aktywna=True).prefetch_related("punkty__glosowanie").first()
    punkty = sesja.punkty.all() if sesja else []

    return render(request, "core/prezydium_agenda.html", {
        "sesja": sesja,
        "punkty": punkty,
    })


# --------------------------------------------------
# Wnioski
# --------------------------------------------------

@login_required
@require_http_methods(["GET", "POST"])
def wnioski_radny(request):
    """Panel radnego do składania i podglądu własnych wniosków w aktywnej sesji.

    Wniosek jest składany do aktualnie aktywnego punktu obrad.
    """
    if request.user.rola != "radny":
        return redirect("prezydium_dashboard")

    sesja = Sesja.objects.filter(aktywna=True).first()
    punkt = None

    if sesja:
        punkt = sesja.punkty.filter(aktywny=True).order_by("numer").first()

    if not sesja or not punkt:
        form = WniosekForm()
        wnioski = Wniosek.objects.none()
        return render(
            request,
            "core/wnioski_radny.html",
            {
                "sesja": sesja,
                "punkt": punkt,
                "form": form,
                "wnioski": wnioski,
            },
        )

    if request.method == "POST":
        form = WniosekForm(request.POST)
        if form.is_valid():
            wniosek = form.save(commit=False)
            wniosek.punkt_obrad = punkt
            wniosek.radny = request.user
            wniosek.save()
            messages.success(request, "Wniosek został złożony.")
            return redirect("wnioski_radny")
    else:
        form = WniosekForm()

    wnioski = (
        Wniosek.objects.filter(punkt_obrad__sesja=sesja, radny=request.user)
        .select_related("punkt_obrad", "radny")
        .order_by("-data")
    )

    return render(
        request,
        "core/wnioski_radny.html",
        {
            "sesja": sesja,
            "punkt": punkt,
            "form": form,
            "wnioski": wnioski,
        },
    )


@login_required
@require_http_methods(["GET"])
def wnioski_prezidium(request):
    """Panel prezydium do przeglądu i zatwierdzania wniosków w aktywnej sesji."""
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = Sesja.objects.filter(aktywna=True).first()
    punkt = None
    if sesja:
        punkt = sesja.punkty.filter(aktywny=True).order_by("numer").first()

    if not sesja:
        return render(request, "core/wnioski_prezidium.html", {"sesja": None, "punkt": None, "wnioski": []})

    qs = Wniosek.objects.filter(punkt_obrad__sesja=sesja).select_related("punkt_obrad", "radny")
    if punkt:
        # domyślnie filtruj do aktywnego punktu, jeśli istnieje
        qs = qs.filter(punkt_obrad=punkt)

    wnioski = qs.order_by("zatwierdzony", "-data")

    return render(
        request,
        "core/wnioski_prezidium.html",
        {
            "sesja": sesja,
            "punkt": punkt,
            "wnioski": wnioski,
        },
    )


@login_required
@require_POST
def wniosek_zatwierdz(request, wniosek_id):
    """Zatwierdź/odrzuć wniosek (toggle) - tylko prezydium."""
    if request.user.rola != "prezydium":
        return HttpResponseForbidden("Brak uprawnień")

    wniosek = get_object_or_404(Wniosek, id=wniosek_id)
    wniosek.zatwierdzony = not wniosek.zatwierdzony
    wniosek.save(update_fields=["zatwierdzony"])

    return redirect("wnioski_prezidium")


@login_required
def glosowanie_ekran(request, glosowanie_id):
    """Pełnoekranowy ekran głosowania (wyniki na żywo) – tylko dla radnych."""
    if request.user.rola != "radny":
        messages.info(request, "Ekran pełnoekranowy jest dostępny tylko dla radnych.")
        return redirect("panel")

    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    punkt = glosowanie.punkt_obrad
    sesja = punkt.sesja

    return render(
        request,
        "core/glosowanie_ekran.html",
        {"sesja": sesja, "punkt": punkt, "glosowanie": glosowanie},
    )


@require_GET
@login_required
def api_glosowanie_status(request, glosowanie_id):
    """API: zwraca status głosowania (otwarte/closed)."""
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    return JsonResponse({"otwarte": glosowanie.otwarte})


@login_required
@require_http_methods(["GET", "POST"])
def reset_danych_testowych(request):
    """Reset danych sesji/głosowań (tylko do testów) – usuwa wszystkie sesje i dane powiązane.

    Bezpieczniki:
    - tylko rola prezydium
    - dodatkowe potwierdzenie frazą w formularzu
    """
    if request.user.rola != "prezydium":
        return redirect("radny")

    if request.method == "POST":
        confirm = (request.POST.get("confirm") or "").strip()
        if confirm != "USUN WSZYSTKO":
            messages.error(request, "Aby wykonać reset wpisz dokładnie: USUN WSZYSTKO")
            return redirect("reset_danych_testowych")

        # kasuj od najniższych zależności
        Glos.objects.all().delete()
        Wniosek.objects.all().delete()
        Glosowanie.objects.all().delete()
        PunktObrad.objects.all().delete()
        Sesja.objects.all().delete()

        messages.success(request, "Usunięto wszystkie sesje, punkty, głosowania, głosy i wnioski. Możesz zacząć od zera.")
        return redirect("prezydium_sesje")

    return render(request, "core/reset_danych_testowych.html")


@login_required
@require_http_methods(["GET"])
def obecnosci_prezidium(request):
    """Panel prezydium do sprawdzania obecności i quorum w aktywnej sesji."""
    if request.user.rola != "prezydium":
        return redirect("radny")

    sesja = Sesja.objects.filter(aktywna=True).first()
    # Uprawnieni: radni + prezydium
    uprawnieni_qs = Uzytkownik.objects.filter(rola__in=["radny", "prezydium"]).order_by("rola", "nazwisko", "imie")
    radni = uprawnieni_qs

    obecnosci_map = {}
    if sesja:
        obecnosci_map = {o.radny_id: o for o in sesja.obecnosci.select_related("radny").all()}

    uprawnieni = radni.count()
    obecni = sum(1 for r in radni if getattr(obecnosci_map.get(r.id), "obecny", False))
    quorum = (uprawnieni // 2) + 1
    jest_quorum = obecni >= quorum

    return render(
        request,
        "core/obecnosci_prezidium.html",
        {
            "sesja": sesja,
            "radni": radni,
            "obecnosci_map": obecnosci_map,
            "uprawnieni": uprawnieni,
            "obecni": obecni,
            "quorum": quorum,
            "jest_quorum": jest_quorum,
        },
    )


@login_required
@require_POST
def ustaw_obecnosc(request):
    """Radny potwierdza obecność w aktywnej sesji."""
    if request.user.rola != "radny":
        return redirect("prezydium_dashboard")

    sesja = Sesja.objects.filter(aktywna=True).first()
    if not sesja:
        messages.error(request, "Brak aktywnej sesji.")
        return redirect("radny")

    obecny = request.POST.get("obecny")
    obecny_flag = True if obecny in ["1", "true", "True", "on"] else False

    from .models import Obecnosc

    Obecnosc.objects.update_or_create(
        sesja=sesja,
        radny=request.user,
        defaults={"obecny": obecny_flag},
    )

    if obecny_flag:
        messages.success(request, "Potwierdzono obecność.")
    else:
        messages.info(request, "Ustawiono status: nieobecny.")

    return redirect("radny")


@login_required
@require_POST
def obecnosci_toggle_prezidium(request, sesja_id, radny_id):
    """Prezydium ręcznie przełącza obecność danego uprawnionego w danej sesji."""
    if request.user.rola != "prezydium":
        return JsonResponse({"error": "Brak uprawnień"}, status=403)

    sesja = get_object_or_404(Sesja, id=sesja_id)
    radny = get_object_or_404(Uzytkownik, id=radny_id, rola__in=["radny", "prezydium"])

    from .models import Obecnosc

    obj, _ = Obecnosc.objects.get_or_create(sesja=sesja, radny=radny)
    obj.obecny = not obj.obecny
    obj.save(update_fields=["obecny", "timestamp"])

    uprawnieni = Uzytkownik.objects.filter(rola__in=["radny", "prezydium"]).count()
    obecni = Obecnosc.objects.filter(sesja=sesja, obecny=True).count()
    quorum = (uprawnieni // 2) + 1

    return JsonResponse({
        "radny_id": radny.id,
        "obecny": obj.obecny,
        "obecni": obecni,
        "uprawnieni": uprawnieni,
        "quorum": quorum,
        "jest_quorum": obecni >= quorum,
    })

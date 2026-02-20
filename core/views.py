from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.db.models import Count, Q
from django.utils import timezone

from .models import Sesja, PunktObrad, Glosowanie, Glos, Wniosek, Komisja, KomisjaSesja, KomisjaPunktObrad, KomisjaWniosek
from .forms import SesjaCreateForm, PunktForm, GlosowanieForm, WniosekForm, KomisjaForm, KomisjaSesjaForm, KomisjaPunktForm, KomisjaWniosekForm
from accounts.models import Uzytkownik


# Helpers (role checks)

def _is_prezydium(user):
    return getattr(user, "rola", None) == "prezydium"


def _is_radny_like(user):
    # roles that can act as a councillor (can vote / see councillor views)
    return getattr(user, "rola", None) in {"radny", "administrator", "prezydium"}


def _can_manage_session(user):
    # session operator permissions: prezydium + administrator
    return getattr(user, "rola", None) in {"prezydium", "administrator"}


def _is_prezydium_or_admin(user):
    return getattr(user, "rola", None) in {"prezydium", "administrator"}


def _radny_like_qs():
    """Queryset of users who are allowed to vote like councillors (excluding prezydium)."""
    return Uzytkownik.objects.filter(rola__in=["radny", "administrator"])


def _uprawnieni_do_glosowania_qs():
    """All users allowed to vote in jawne vote list / quorum.

    In this project it includes councillors (radny + administrator) and prezydium.
    """
    return Uzytkownik.objects.filter(rola__in=["radny", "administrator", "prezydium"])


# --------------------------------------------------
# Wspólny panel startowy
# --------------------------------------------------

@login_required
def panel(request):
    """
    Po zalogowaniu kieruje:
    - prezydium -> dashboard prezydium
    - administrator -> agenda/sesje (zarządzanie przebiegiem)
    - radny -> panel radnego z listą głosowań
    """
    if _is_prezydium(request.user):
        return redirect("prezydium_dashboard")
    if request.user.rola == "administrator":
        return redirect("prezydium_agenda")
    return redirect("radny")


def landing(request):
    """Public landing page.

    - pokazuje opis systemu
    - dopiero potem CTA do logowania
    - jeżeli użytkownik jest zalogowany, przekieruj do panelu
    """
    if request.user.is_authenticated:
        return redirect("panel")

    return render(request, "core/landing.html")


@login_required
def pomoc(request):
    """Strona pomocy (FAQ + skróty).

    Celowo prosta: jeden template, bez logiki biznesowej.
    """
    return render(request, "core/pomoc.html")


# --------------------------------------------------
# Widoki PREZYDIUM
# --------------------------------------------------

@login_required
def prezydium_dashboard(request):
    """
    Prosty dashboard: pokazuje najbliższą sesję, liczbę punktów i otwartych głosowań.
    """
    if not _is_prezydium(request.user):
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
    if not _can_manage_session(request.user):
        return redirect("radny")

    sesje = Sesja.objects.all().order_by("-data")
    return render(request, "core/prezydium_sesje.html", {"sesje": sesje})


@login_required
def sesja_nowa(request):
    """
    Kreator tworzenia nowej sesji – po zapisaniu przekierowuje do edycji sesji.
    """
    if not _can_manage_session(request.user):
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
    if not _can_manage_session(request.user):
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
    if not _can_manage_session(request.user):
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
    if not _can_manage_session(request.user):
        return redirect("radny")

    sesja = get_object_or_404(Sesja, id=sesja_id)
    sesja.aktywna = False
    sesja.save()
    messages.success(request, "Sesja została dezaktywowana.")
    return redirect("prezydium_sesje")


@login_required
@require_POST
def usun_sesje(request, sesja_id):
    if not _can_manage_session(request.user):
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
    if not _can_manage_session(request.user):
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
    if not _can_manage_session(request.user):
        return redirect("radny")

    sesje = Sesja.objects.all().prefetch_related("punkty__glosowanie")
    return render(request, "core/prezidium.html", {"sesje": sesje})


@login_required
def nadchodzace_sesje_prezidium(request):
    """
    Prosta lista sesji (np. aktywnych lub wszystkich) – wykorzystasz w menu 'Nadchodzące sesje'.
    Na razie pokazuje wszystkie sesje posortowane rosnąco po dacie.
    """
    if not _can_manage_session(request.user):
        return redirect("radny")

    sesje = Sesja.objects.all().order_by("data")
    return render(request, "core/nadchodzace_sesje_prezidium.html", {"sesje": sesje})


@login_required
def prezydium_uczestnicy(request):
    """Lista wszystkich radnych (dla prezydium i administratorów).

    W praktyce „radni” w UI to wszyscy uprawnieni do głosowania:
    - radny
    - prezydium
    - administrator (też jest radnym)
    """
    if not _is_prezydium_or_admin(request.user):
        return HttpResponseForbidden("Brak uprawnień")

    radni = _uprawnieni_do_glosowania_qs().order_by("nazwisko", "imie")
    return render(request, "core/prezydium_uczestnicy.html", {"radni": radni})


@login_required
def prezydium_uczestnik_szczegoly(request, user_id: int):
    """Szczegóły wybranego uczestnika (dla prezydium i administratorów)."""
    if not _is_prezydium_or_admin(request.user):
        return HttpResponseForbidden("Brak uprawnień")

    # Dopuszczamy podgląd także prezydium i administratorów,
    # bo są częścią listy i mają status „radny” w sensie uprawnień do głosowania.
    radny = get_object_or_404(
        Uzytkownik,
        id=user_id,
        rola__in=["radny", "administrator", "prezydium"],
    )

    return render(request, "core/prezydium_uczestnik_szczegoly.html", {"radny": radny})


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
    if not _is_radny_like(request.user):
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
@require_http_methods(["GET", "POST"])
def toggle_glosowanie(request, glosowanie_id):
    """Otwieranie / zamykanie głosowania – prezydium lub administrator.

    Preferowane jest POST (bezpieczniejsze). Dla kompatybilności
    stary JS używający GET nadal zadziała.
    """
    if not _can_manage_session(request.user):
        return JsonResponse({"error": "Brak uprawnień"}, status=403)

    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    glosowanie.otwarte = not glosowanie.otwarte
    glosowanie.save(update_fields=["otwarte"])
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

    # Uprawnieni do oddania głosu (radny + administrator + prezydium)
    if getattr(request.user, "rola", None) not in {"radny", "administrator", "prezydium"}:
        if is_ajax(request):
            return JsonResponse({"error": "Brak uprawnień do głosowania"}, status=403)
        return HttpResponseForbidden("Brak uprawnień do głosowania")

    if not glosowanie.otwarte:
        if is_ajax(request):
            return JsonResponse({"error": "Głosowanie zamknięte"}, status=400)
        messages.error(request, "Głosowanie jest zamknięte.")
        return redirect("panel")

    wartosc = request.POST.get("glos")
    if wartosc not in ["za", "przeciw", "wstrzymuje"]:
        if is_ajax(request):
            return JsonResponse({"error": "Nieprawidłowa wartość głosu"}, status=400)
        messages.error(request, "Nieprawidłowa wartość głosu.")
        return redirect("panel")

    glos, created = Glos.objects.get_or_create(
        glosowanie=glosowanie,
        uzytkownik=request.user,
        defaults={"glos": wartosc},
    )

    if not created:
        if is_ajax(request):
            return JsonResponse({"error": "Już oddałeś głos w tym głosowaniu"}, status=409)
        messages.warning(request, "Już oddałeś głos w tym głosowaniu.")
        return redirect("panel")

    if is_ajax(request):
        return JsonResponse({"success": True})

    messages.success(request, "Głos został zapisany.")
    return redirect("panel")


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

    uprawnieni = _uprawnieni_do_glosowania_qs().order_by("nazwisko", "imie")
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


@login_required
def sesja_ekran_aktywna(request):
    """Łatwy entrypoint do ekranu sesji.

    Użycie: /ekran/sesja/
    - gdy istnieje aktywna sesja -> przekieruj na ekran tej sesji
    - gdy brak aktywnej sesji -> wróć do agendy/panelu z komunikatem
    """
    sesja = Sesja.objects.filter(aktywna=True).order_by("-data").first()
    if not sesja:
        messages.warning(request, "Brak aktywnej sesji. Ustaw sesję jako aktywną.")
        if _can_manage_session(request.user):
            return redirect("prezydium_agenda")
        return redirect("panel")

    return redirect("sesja_ekran", sesja_id=sesja.id)


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
    if not _can_manage_session(request.user):
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
    if not _can_manage_session(request.user):
        return redirect("radny")

    sesja = Sesja.objects.filter(aktywna=True).prefetch_related("punkty__glosowanie").first()
    punkty = sesja.punkty.all() if sesja else []

    return render(request, "core/prezydium_agenda.html", {
        "sesja": sesja,
        "punkty": punkty,
    })


@login_required
def admin_sesja_panel(request):
    """Panel sterowania sesją dla administratora.

    Wymaganie: w jednym miejscu administrator ma:
    - przełączanie aktywnego punktu obrad,
    - otwieranie/zamykanie głosowania.

    Technicznie wykorzystuje te same dane co agenda prezydium.
    """
    if getattr(request.user, "rola", None) != "administrator":
        return redirect("panel")
    # współdzielony ekran z prezydium (render ten sam template)
    return prezydium_agenda(request)


# --------------------------------------------------
# Wnioski
# --------------------------------------------------

@login_required
@require_http_methods(["GET", "POST"])
def wnioski_radny(request):
    """Panel radnego do składania i podglądu własnych wniosków.

    Wniosek może być:
    - przypięty do aktywnego punktu (jeśli istnieje), albo
    - złożony poza sesją (punkt_obrad=NULL), nawet gdy sesja jest aktywna.

    System automatycznie nadaje sygnaturę przy zapisie.
    """
    if not _is_radny_like(request.user):
        return redirect("prezydium_dashboard")

    sesja = Sesja.objects.filter(aktywna=True).first()
    punkt = None
    if sesja:
        punkt = sesja.punkty.filter(aktywny=True).order_by("numer").first()

    if request.method == "POST":
        form = WniosekForm(request.POST)
        if form.is_valid():
            wniosek = form.save(commit=False)

            # jeśli użytkownik zaznaczy "poza sesją" lub nie ma aktywnego punktu
            poza_sesja = (request.POST.get("poza_sesja") in ["1", "true", "True", "on"]) \
                         or (punkt is None)
            wniosek.punkt_obrad = None if poza_sesja else punkt

            wniosek.radny = request.user
            wniosek.save()
            messages.success(request, f"Wniosek został złożony. Sygnatura: {wniosek.sygnatura}")
            return redirect("wnioski_radny")
    else:
        form = WniosekForm()

    wnioski = (
        Wniosek.objects.filter(radny=request.user)
        .select_related("punkt_obrad", "punkt_obrad__sesja")
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
            "mozna_przypiac": punkt is not None,
        },
    )


@login_required
@require_http_methods(["GET"])
def wnioski_prezidium(request):
    """Panel prezydium do przeglądu i zatwierdzania wniosków w aktywnej sesji."""
    if not _is_prezydium(request.user):
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
    if not _is_prezydium(request.user):
        return HttpResponseForbidden("Brak uprawnień")

    wniosek = get_object_or_404(Wniosek, id=wniosek_id)
    wniosek.zatwierdzony = not wniosek.zatwierdzony
    wniosek.save(update_fields=["zatwierdzony"])

    return redirect("wnioski_prezidium")


@login_required
def glosowanie_ekran(request, glosowanie_id):
    """Pełnoekranowy ekran głosowania (wyniki na żywo) – dla radnych (radny + administrator)."""
    if not _is_radny_like(request.user):
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
    # Uprawnieni: radni + administrator + prezydium
    uprawnieni_qs = _uprawnieni_do_glosowania_qs().order_by("rola", "nazwisko", "imie")
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
    """Radny potwierdza obecność w aktywnej sesji.

    Zasada:
    - radny może zgłosić obecność/nieobecność tylko raz (pierwszy zapis dla danej sesji)
    - po zgłoszeniu, zmiany może dokonywać wyłącznie prezydium
    """
    if not _is_radny_like(request.user):
        return redirect("prezydium_dashboard")

    sesja = Sesja.objects.filter(aktywna=True).first()
    if not sesja:
        messages.error(request, "Brak aktywnej sesji.")
        return redirect("radny")

    from .models import Obecnosc

    # jeśli już zgłoszono obecność/nieobecność, blokujemy zmianę przez radnego
    if Obecnosc.objects.filter(sesja=sesja, radny=request.user).exists():
        messages.warning(request, "Status obecności został już zgłoszony. Zmiany może wprowadzić tylko prezydium.")
        return redirect("radny")

    obecny = request.POST.get("obecny")
    obecny_flag = True if obecny in ["1", "true", "True", "on"] else False

    Obecnosc.objects.create(
        sesja=sesja,
        radny=request.user,
        obecny=obecny_flag,
    )

    if obecny_flag:
        messages.success(request, "Potwierdzono obecność.")
    else:
        messages.info(request, "Zgłoszono nieobecność.")

    return redirect("radny")


@login_required
@require_POST
def obecnosci_toggle_prezidium(request, sesja_id, radny_id):
    """Prezydium ręcznie przełącza obecność danego uprawnionego w danej sesji."""
    if request.user.rola != "prezydium":
        return JsonResponse({"error": "Brak uprawnień"}, status=403)

    sesja = get_object_or_404(Sesja, id=sesja_id)
    radny = get_object_or_404(Uzytkownik, id=radny_id, rola__in=["radny", "administrator", "prezydium"])

    from .models import Obecnosc

    obj, _ = Obecnosc.objects.get_or_create(sesja=sesja, radny=radny)
    obj.obecny = not obj.obecny
    obj.save(update_fields=["obecny", "timestamp"])

    uprawnieni = _uprawnieni_do_glosowania_qs().count()
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


# --------------------------------------------------
# Widoki KOMISJI
# --------------------------------------------------

@login_required
def komisje_moje(request):
    if request.user.rola not in ["radny", "administrator", "prezydium"]:
        return redirect("panel")

    komisje = Komisja.objects.filter(Q(czlonkowie=request.user) | Q(przewodniczacy=request.user)).distinct()
    return render(request, "core/komisje_moje.html", {"komisje": komisje})


@login_required
def komisja_szczegoly(request, komisja_id):
    komisja = get_object_or_404(Komisja, id=komisja_id)
    if request.user not in komisja.czlonkowie.all() and request.user != komisja.przewodniczacy and request.user.rola != "prezydium":
        return HttpResponseForbidden("Brak uprawnień")

    sesje = komisja.sesje.all()
    return render(request, "core/komisja_szczegoly.html", {"komisja": komisja, "sesje": sesje})


@login_required
@require_http_methods(["GET", "POST"])
def komisja_wnioski(request, komisja_id):
    komisja = get_object_or_404(Komisja, id=komisja_id)
    if request.user not in komisja.czlonkowie.all() and request.user != komisja.przewodniczacy:
        return HttpResponseForbidden("Brak uprawnień")

    if request.method == "POST":
        form = KomisjaWniosekForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.komisja = komisja
            obj.autor = request.user
            obj.save()
            messages.success(request, "Wniosek komisji zapisany.")
            return redirect("komisja_wnioski", komisja_id=komisja.id)
    else:
        form = KomisjaWniosekForm()

    wnioski = komisja.wnioski.select_related("autor").all()
    return render(request, "core/komisja_wnioski.html", {"komisja": komisja, "form": form, "wnioski": wnioski})


@login_required
def komisja_skrzynka_rady(request):
    """Skrzynka prezydium: wnioski komisji do zatwierdzenia/wysłania do rady."""
    if not _is_prezydium(request.user):
        return HttpResponseForbidden("Brak uprawnień")

    qs = KomisjaWniosek.objects.select_related("komisja", "autor").all()
    return render(request, "core/komisja_skrzynka_rady.html", {"wnioski": qs})


@login_required
@require_POST
def komisja_wniosek_wyslij_do_rady(request, wniosek_id):
    if not _is_prezydium(request.user):
        return HttpResponseForbidden("Brak uprawnień")

    obj = get_object_or_404(KomisjaWniosek, id=wniosek_id)
    obj.zatwierdzony_przez_prezydium = True
    obj.data_zatwierdzenia = timezone.now()
    obj.wyslany_do_rady = True
    obj.data_wyslania = timezone.now()
    obj.save(update_fields=["zatwierdzony_przez_prezydium", "data_zatwierdzenia", "wyslany_do_rady", "data_wyslania"])

    messages.success(request, "Wniosek komisji został wysłany do rady.")
    return redirect("komisja_skrzynka_rady")


@login_required
@require_GET
def wnioski_radny_pdf(request):
    if not _is_radny_like(request.user):
        return redirect("prezydium_dashboard")

    wnioski = (
        Wniosek.objects.filter(radny=request.user)
        .select_related("punkt_obrad", "punkt_obrad__sesja", "radny")
        .order_by("-data")
    )

    return _wnioski_pdf_response(
        title=f"Wnioski radnego: {request.user.imie} {request.user.nazwisko}",
        wnioski=list(wnioski),
        filename="wnioski_moje.pdf",
    )


@login_required
@require_GET
def wniosek_pdf(request, wniosek_id):
    """PDF pojedynczego wniosku.

    Dostęp:
    - radny: tylko własny
    - prezydium: wszystkie
    """
    w = get_object_or_404(Wniosek, id=wniosek_id)

    if _is_radny_like(request.user) and w.radny_id != request.user.id and not _is_prezydium(request.user):
        return HttpResponseForbidden("Brak uprawnień")
    if request.user.rola not in ["radny", "administrator", "prezydium"]:
        return HttpResponseForbidden("Brak uprawnień")

    safe_sig = (w.sygnatura or str(w.id)).replace("/", "-")
    return _wnioski_pdf_response(
        title=f"Wniosek {w.sygnatura}",
        wnioski=[w],
        filename=f"wniosek_{safe_sig}.pdf",
    )


def _wnioski_pdf_response(*, title: str, wnioski: list[Wniosek], filename: str):
    """Generuje PDF dla listy wniosków. Wykorzystuje ReportLab."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    # fonty z obsługą polskich znaków (TTF)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Rejestracja fontu (jeśli plik istnieje)
    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"
    try:
        import os
        from django.conf import settings

        font_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "fonts", "DejaVuSans.ttf")
        font_bold_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "fonts", "DejaVuSans-Bold.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
            font_regular = "DejaVuSans"
        if os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_bold_path))
            font_bold = "DejaVuSans-Bold"
    except Exception:
        # fallback do Helvetica (bez PL znaków) jeśli coś pójdzie nie tak
        pass

    y = height - 20 * mm
    c.setFont(font_bold, 14)
    c.drawString(20 * mm, y, title)
    y -= 10 * mm

    c.setFont(font_regular, 9)
    c.drawString(20 * mm, y, f"Wygenerowano: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 12 * mm

    for w in wnioski:
        if y < 25 * mm:
            c.showPage()
            y = height - 20 * mm

        c.setFont(font_bold, 11)
        c.drawString(20 * mm, y, f"Sygnatura: {w.sygnatura}   |   Typ: {w.get_typ_display()}   |   Data: {w.data.strftime('%Y-%m-%d %H:%M')}")
        y -= 6 * mm

        c.setFont(font_regular, 10)
        c.drawString(20 * mm, y, f"Autor: {w.radny.imie} {w.radny.nazwisko}")
        y -= 6 * mm

        if w.punkt_obrad_id:
            sesja_nazwa = getattr(getattr(w.punkt_obrad, "sesja", None), "nazwa", "")
            c.setFont(font_regular, 9)
            c.drawString(20 * mm, y, f"Sesja: {sesja_nazwa} | Punkt: {w.punkt_obrad.numer}. {w.punkt_obrad.tytul}")
            y -= 6 * mm
        else:
            c.setFont(font_regular, 9)
            c.drawString(20 * mm, y, "Poza sesją")
            y -= 6 * mm

        # treść (proste łamanie wierszy)
        c.setFont(font_regular, 10)
        max_chars = 110
        text = (w.tresc or "").replace("\r\n", "\n").replace("\r", "\n")
        for para in text.split("\n"):
            para = para.strip()
            if not para:
                y -= 4 * mm
                continue
            while len(para) > max_chars:
                line = para[:max_chars]
                para = para[max_chars:]
                c.drawString(20 * mm, y, line)
                y -= 5 * mm
                if y < 25 * mm:
                    c.showPage()
                    y = height - 20 * mm
                    c.setFont(font_regular, 10)
            c.drawString(20 * mm, y, para)
            y -= 5 * mm
            if y < 25 * mm:
                c.showPage()
                y = height - 20 * mm
                c.setFont(font_regular, 10)

        y -= 6 * mm

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@login_required
@require_GET
def protokol_sesji_pdf(request):
    """Podstawowy protokół PDF dla aktywnej sesji.

    Zawiera:
    - nagłówek (nazwa sesji, data)
    - listę punktów
    - podsumowania głosowań (za/przeciw/wstrzymuje, typ większości, czy przeszło)

    Dostęp: prezydium oraz administrator.
    """
    if not _can_manage_session(request.user):
        return HttpResponseForbidden("Brak uprawnień")

    sesja = Sesja.objects.filter(aktywna=True).first()
    if not sesja:
        return HttpResponse("Brak aktywnej sesji.", content_type="text/plain")

    punkty = (
        sesja.punkty
        .select_related("glosowanie")
        .order_by("numer")
    )

    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # fonty PL (jak w _wnioski_pdf_response)
    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"
    try:
        import os
        from django.conf import settings

        font_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "fonts", "DejaVuSans.ttf")
        font_bold_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "fonts", "DejaVuSans-Bold.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
            font_regular = "DejaVuSans"
        if os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_bold_path))
            font_bold = "DejaVuSans-Bold"
    except Exception:
        pass

    # Marginesy: 20 mm z każdej strony
    margin_left = 20 * mm
    margin_right = 20 * mm
    margin_top = 20 * mm
    margin_bottom = 20 * mm
    usable_width = width - margin_left - margin_right

    def new_page(y_start=None):
        c.showPage()
        y0 = (height - margin_top) if y_start is None else y_start
        return y0

    y = height - margin_top

    c.setFont(font_bold, 14)
    c.drawString(margin_left, y, "Protokół z posiedzenia")
    y -= 8 * mm

    c.setFont(font_bold, 12)
    c.drawString(margin_left, y, sesja.nazwa)
    y -= 6 * mm

    c.setFont(font_regular, 10)
    c.drawString(margin_left, y, f"Data: {timezone.localtime(sesja.data).strftime('%Y-%m-%d %H:%M')}")
    y -= 6 * mm

    c.setFont(font_regular, 9)
    c.drawString(margin_left, y, f"Wygenerowano: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 10 * mm

    c.setFont(font_bold, 11)
    c.drawString(margin_left, y, "Porządek obrad i wyniki głosowań")
    y -= 8 * mm

    for p in punkty:
        if y < margin_bottom:
            y = new_page()

        c.setFont(font_bold, 10)
        c.drawString(margin_left, y, f"{p.numer}. {p.tytul}")
        y -= 5 * mm

        if p.opis:
            c.setFont(font_regular, 9)
            text = (p.opis or "").replace("\r\n", "\n").replace("\r", "\n")
            for para in text.split("\n"):
                para = para.strip()
                if not para:
                    y -= 3 * mm
                    continue
                # Łamanie linii na podstawie szerokości
                while para:
                    # Oblicz ile znaków zmieści się w usable_width
                    max_chars = len(para)
                    for i in range(1, len(para)+1):
                        if c.stringWidth(para[:i], font_regular, 9) > usable_width - 2 * mm:
                            max_chars = i - 1
                            break
                    line, para = para[:max_chars], para[max_chars:]
                    c.drawString(margin_left + 2 * mm, y, line)
                    y -= 4.5 * mm
                    if y < margin_bottom:
                        y = new_page()
                        c.setFont(font_regular, 9)

        gl = getattr(p, "glosowanie", None)
        if gl:
            r = gl.wynik_podsumowanie()
            c.setFont(font_regular, 9)
            meta = f"Głosowanie: {gl.nazwa} | Jawność: {gl.get_jawnosc_display()} | Większość: {gl.get_wiekszosc_display()}"
            # Łamanie linii meta jeśli za długa
            meta_lines = []
            meta_text = meta
            while meta_text:
                max_chars = len(meta_text)
                for i in range(1, len(meta_text)+1):
                    if c.stringWidth(meta_text[:i], font_regular, 9) > usable_width - 2 * mm:
                        max_chars = i - 1
                        break
                line, meta_text = meta_text[:max_chars], meta_text[max_chars:]
                meta_lines.append(line)
            for line in meta_lines:
                c.drawString(margin_left + 2 * mm, y, line)
                y -= 4.8 * mm
            y -= 4.8 * mm

            wynik = f"Za: {r['za']}  Przeciw: {r['przeciw']}  Wstrzymuje: {r['wstrzymuje']}"
            if r.get("prog"):
                wynik += f"  |  Próg: {r['prog']}"
            wynik += f"  |  Wynik: {'PRZESZŁO' if r['przeszedl'] else 'NIE PRZESZŁO'}"
            # Łamanie linii wynik jeśli za długa
            wynik_lines = []
            wynik_text = wynik
            while wynik_text:
                max_chars = len(wynik_text)
                for i in range(1, len(wynik_text)+1):
                    if c.stringWidth(wynik_text[:i], font_regular, 9) > usable_width - 2 * mm:
                        max_chars = i - 1
                        break
                line, wynik_text = wynik_text[:max_chars], wynik_text[max_chars:]
                wynik_lines.append(line)
            for line in wynik_lines:
                c.drawString(margin_left + 2 * mm, y, line)
                y -= 6 * mm
            y -= 6 * mm
        else:
            c.setFont(font_regular, 9)
            c.drawString(margin_left + 2 * mm, y, "Brak głosowania")
            y -= 6 * mm

        y -= 2 * mm

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()

    safe_name = (sesja.nazwa or "sesja").replace("/", "-")
    filename = f"protokol_{safe_name}_{timezone.localtime(sesja.data).strftime('%Y-%m-%d')}.pdf"

    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    return resp

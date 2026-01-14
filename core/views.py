from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Count

from .models import Sesja, PunktObrad, Glosowanie, Glos
from .forms import SesjaCreateForm, PunktForm, GlosowanieForm, WniosekForm


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
    """
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    if not glosowanie.otwarte:
        return JsonResponse({"error": "Głosowanie zamknięte"})

    wartosc = request.POST.get("glos")
    if wartosc not in ["za", "przeciw", "wstrzymuje"]:
        return JsonResponse({"error": "Nieprawidłowa wartość głosu"})

    glos, created = Glos.objects.get_or_create(
        glosowanie=glosowanie,
        uzytkownik=request.user,
        defaults={"glos": wartosc},
    )

    if not created:
        return JsonResponse({"error": "Już oddałeś głos w tym głosowaniu"})

    return JsonResponse({"success": True})


def api_wyniki(request, glosowanie_id):
    """
    API z podsumowaniem wyników głosowania (Za / Przeciw / Wstrzymuję).
    """
    glosowanie = get_object_or_404(Glosowanie, id=glosowanie_id)
    wyniki = (
        Glos.objects.filter(glosowanie=glosowanie)
        .values("glos")
        .annotate(count=Count("glos"))
    )

    dane = {"za": 0, "przeciw": 0, "wstrzymuje": 0}
    for wynik in wyniki:
        dane[wynik["glos"]] = wynik["count"]

    return JsonResponse(dane)


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

from django.views.decorators.http import require_GET
from django.utils import timezone
from django.db.models import Q

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

    # Tu możesz dopasować logikę wyboru aktywnego punktu:
    # np. dodatkowe pole 'aktywny' w modelu PunktObrad.
    punkt = (
        sesja.punkty.filter(Q(aktywny=True) | Q())  # TODO: dopasuj do swojej logiki
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
# SEO :>
# --------------------------------------------------

@require_GET
def robots_txt(request):
    """
    Dynamicznie generuje robots.txt
    """
    lines = [
        "User-agent: *",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
        "",
        "# Prywatne ścieżki - zablokowane dla botów",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /private/",
        "Disallow: /api/",
        "",
        "# Publiczne ścieżki - dozwolone",
        "Allow: /$",
        "Allow: /radny/",
        "Allow: /wyniki/",
        "Allow: /panel/",
        "Allow: /prezydium/",
    ]
    
    # blockdev
    from django.conf import settings
    if settings.DEBUG:
        lines.insert(2, "Disallow: /")
    
    return HttpResponse("\n".join(lines), content_type="text/plain")


# --------------------------------------------------
# Sitemap - Klasy
# --------------------------------------------------

class StaticViewSitemap(Sitemap):
    """Sitemap dla statycznych stron"""
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        return [
            'panel',  # panel
            'radny',  # radny_panel
            'wyniki_publiczne',  # wyniki
            'prezydium_dashboard',  # prezydium
            'nadchodzace_sesje_prezidium',  # nadchodzące sesje
        ]
    
    def location(self, item):
        return reverse(item)
    
    def lastmod(self, item):

        return timezone.now()


class SessionSitemap(Sitemap):
    """Sitemap dla sesji"""
    changefreq = "monthly"
    priority = 0.7
    
    def items(self):
        return Sesja.objects.filter(
            data__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-data')
    
    def location(self, obj):
        return reverse('nadchodzace_sesje_prezidium')
    
    def lastmod(self, obj):
        return obj.updated_at or obj.created_at


class PunktSitemap(Sitemap):
    """Sitemap dla punktów obrad"""
    changefreq = "weekly"
    priority = 0.6
    
    def items(self):
        return PunktObrad.objects.filter(
            sesja__aktywna=True
        ).select_related('sesja').order_by('-sesja__data')
    
    def location(self, obj):
        return reverse('porzadek_obrad_prezidium')
    
    def lastmod(self, obj):
        return obj.updated_at or obj.created_at


sitemaps = {
    'static': StaticViewSitemap,
    'sessions': SessionSitemap,
    'punkty': PunktSitemap,
}


# --------------------------------------------------
# Dynamiczny sitemap
# --------------------------------------------------

@require_GET
def dynamic_sitemap(request):
    """
    Dynamicznie generuje sitemap.xml z auto-discovery URL
    """
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    
    base_url = f"{request.scheme}://{request.get_host()}"
    now = datetime.now().strftime('%Y-%m-%d')
    
    base_urls = [
        {'loc': '', 'name': 'panel', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': 'radny/', 'name': 'radny', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': 'prezydium/dashboard/', 'name': 'prezydium_dashboard', 'priority': '0.8', 'changefreq': 'daily'},
        {'loc': 'prezydium/sesje/', 'name': 'prezydium_sesje', 'priority': '0.7', 'changefreq': 'weekly'},
        {'loc': 'wyniki/', 'name': 'wyniki_publiczne', 'priority': '0.8', 'changefreq': 'daily'},
        {'loc': 'prezydium/agenda/', 'name': 'prezydium_agenda', 'priority': '0.7', 'changefreq': 'daily'},
        {'loc': 'prezydium/nadchodzace/', 'name': 'nadchodzace_sesje_prezidium', 'priority': '0.7', 'changefreq': 'weekly'},
    ]
    
    #  URL
    for url_info in base_urls:
        url_elem = ET.SubElement(root, "url")
        ET.SubElement(url_elem, "loc").text = f"{base_url}/{url_info['loc']}"
        ET.SubElement(url_elem, "lastmod").text = now
        ET.SubElement(url_elem, "changefreq").text = url_info['changefreq']
        ET.SubElement(url_elem, "priority").text = url_info['priority']
    
    try:
        sesje = Sesja.objects.filter(
            data__gte=timezone.now() - timezone.timedelta(days=365)
        )[:100]  
        
        for sesja in sesje:
            url_elem = ET.SubElement(root, "url")
            ET.SubElement(url_elem, "loc").text = f"{base_url}/sesja/{sesja.id}/"
            lastmod = sesja.updated_at or sesja.created_at
            ET.SubElement(url_elem, "lastmod").text = lastmod.strftime('%Y-%m-%d')
            ET.SubElement(url_elem, "changefreq").text = "monthly"
            ET.SubElement(url_elem, "priority").text = "0.6"
    except Exception as e:
        print(f"Błąd przy dodawaniu sesji do sitemap: {e}")
    
    try:
        punkty = PunktObrad.objects.filter(
            sesja__aktywna=True
        ).select_related('sesja')[:100]
        
        for punkt in punkty:
            url_elem = ET.SubElement(root, "url")
            ET.SubElement(url_elem, "loc").text = f"{base_url}/punkt/{punkt.id}/"
            lastmod = punkt.updated_at or punkt.created_at
            ET.SubElement(url_elem, "lastmod").text = lastmod.strftime('%Y-%m-%d')
            ET.SubElement(url_elem, "changefreq").text = "weekly"
            ET.SubElement(url_elem, "priority").text = "0.5"
    except Exception as e:
        print(f"Błąd przy dodawaniu punktów do sitemap: {e}")
    
    # XML
    xml_string = ET.tostring(root, encoding='unicode', method='xml')
    
    response = HttpResponse(xml_string, content_type='application/xml')
    return response
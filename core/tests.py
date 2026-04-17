from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Uzytkownik
from core.models import Sesja, PunktObrad, Glosowanie, Obecnosc, Glos, Komisja, KomisjaSesja, KomisjaWniosek, KomisjaPunktObrad, KomisjaGlosowanie, KomisjaGlos


class AuthorizationMatrixTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.radny = Uzytkownik.objects.create_user(
			username="radny",
			password="test12345",
			rola="radny",
			imie="Jan",
			nazwisko="Radny",
		)
		cls.prezydium = Uzytkownik.objects.create_user(
			username="prezydium",
			password="test12345",
			rola="prezydium",
			imie="Anna",
			nazwisko="Prezydium",
		)
		cls.admin = Uzytkownik.objects.create_user(
			username="adminrole",
			password="test12345",
			rola="administrator",
			imie="Adam",
			nazwisko="Admin",
		)

		sesja = Sesja.objects.create(
			nazwa="Sesja testowa",
			data=timezone.now(),
			aktywna=True,
		)
		punkt = PunktObrad.objects.create(
			sesja=sesja,
			numer=1,
			tytul="Punkt testowy",
		)
		cls.glosowanie = Glosowanie.objects.create(
			punkt_obrad=punkt,
			nazwa="Głosowanie testowe",
			otwarte=False,
		)

	def _login(self, user):
		self.client.force_login(user)

	def test_prezydium_sesje_access_matrix(self):
		url = reverse("prezydium_sesje")

		self._login(self.prezydium)
		self.assertEqual(self.client.get(url).status_code, 200)

		self._login(self.admin)
		self.assertEqual(self.client.get(url).status_code, 200)

		self._login(self.radny)
		response = self.client.get(url)
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, reverse("radny"))

	def test_prezydium_uczestnicy_access_matrix(self):
		url = reverse("prezydium_uczestnicy")

		self._login(self.prezydium)
		self.assertEqual(self.client.get(url).status_code, 200)

		self._login(self.admin)
		self.assertEqual(self.client.get(url).status_code, 200)

		self._login(self.radny)
		self.assertEqual(self.client.get(url).status_code, 403)

	def test_wnioski_prezidium_only_prezydium(self):
		url = reverse("wnioski_prezidium")

		self._login(self.prezydium)
		self.assertEqual(self.client.get(url).status_code, 200)

		self._login(self.admin)
		response_admin = self.client.get(url)
		self.assertEqual(response_admin.status_code, 302)
		self.assertRedirects(response_admin, reverse("radny"))

		self._login(self.radny)
		response_radny = self.client.get(url)
		self.assertEqual(response_radny.status_code, 302)
		self.assertRedirects(response_radny, reverse("radny"))

	def test_toggle_glosowanie_access_matrix(self):
		url = reverse("toggle_glosowanie", args=[self.glosowanie.id])

		self._login(self.prezydium)
		response_prezydium = self.client.get(url)
		self.assertEqual(response_prezydium.status_code, 200)
		self.assertIn("otwarte", response_prezydium.json())

		self._login(self.admin)
		response_admin = self.client.get(url)
		self.assertEqual(response_admin.status_code, 200)
		self.assertIn("otwarte", response_admin.json())

		self._login(self.radny)
		response_radny = self.client.get(url)
		self.assertEqual(response_radny.status_code, 403)
		self.assertEqual(response_radny.json().get("error"), "Brak uprawnień")


class AttendanceButtonsVisibilityTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.radny = Uzytkownik.objects.create_user(
			username="radny_obecnosc",
			password="test12345",
			rola="radny",
			imie="Olga",
			nazwisko="Nowak",
		)
		cls.sesja = Sesja.objects.create(
			nazwa="Sesja obecności",
			data=timezone.now(),
			aktywna=True,
		)

	def test_buttons_visible_before_attendance_submission(self):
		self.client.force_login(self.radny)
		response = self.client.get(reverse("radny"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Potwierdź obecność")
		self.assertContains(response, "Zgłoś nieobecność")

	def test_buttons_hidden_after_attendance_submission(self):
		Obecnosc.objects.create(
			sesja=self.sesja,
			radny=self.radny,
			obecny=True,
		)
		self.client.force_login(self.radny)
		response = self.client.get(reverse("radny"))

		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Potwierdź obecność")
		self.assertNotContains(response, "Zgłoś nieobecność")
		self.assertContains(response, "Obecność potwierdzona")


class VotingButtonsVisibilityTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.radny = Uzytkownik.objects.create_user(
			username="radny_glos",
			password="test12345",
			rola="radny",
			imie="Marek",
			nazwisko="Głosujący",
		)
		sesja = Sesja.objects.create(
			nazwa="Sesja głosowania",
			data=timezone.now(),
			aktywna=True,
		)
		punkt = PunktObrad.objects.create(
			sesja=sesja,
			numer=1,
			tytul="Punkt głosowania",
		)
		cls.glosowanie = Glosowanie.objects.create(
			punkt_obrad=punkt,
			nazwa="Głosowanie jawne",
			otwarte=True,
			typ="zwykle",
		)

	def test_voting_buttons_visible_before_vote(self):
		self.client.force_login(self.radny)
		response = self.client.get(reverse("radny"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'name="glos" value="za"')
		self.assertContains(response, 'name="glos" value="przeciw"')
		self.assertContains(response, 'name="glos" value="wstrzymuje"')

	def test_voting_buttons_hidden_after_vote(self):
		Glos.objects.create(
			glosowanie=self.glosowanie,
			uzytkownik=self.radny,
			glos="za",
		)
		self.client.force_login(self.radny)
		response = self.client.get(reverse("radny"))

		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, 'name="glos" value="za"')
		self.assertNotContains(response, 'name="glos" value="przeciw"')
		self.assertNotContains(response, 'name="glos" value="wstrzymuje"')
		self.assertContains(response, "Już oddałeś głos w tym głosowaniu")


class SessionEditingAndAgendaTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.prezydium = Uzytkownik.objects.create_user(
			username="prezydium_edit",
			password="test12345",
			rola="prezydium",
			imie="Ewa",
			nazwisko="Edytor",
		)
		cls.sesja = Sesja.objects.create(
			nazwa="Sesja edycji",
			data=timezone.now(),
			aktywna=False,
		)
		cls.punkt = PunktObrad.objects.create(
			sesja=cls.sesja,
			numer=1,
			tytul="Punkt edytowany",
			aktywny=True,
		)

	def test_session_edit_saves_datetime_and_description(self):
		self.client.force_login(self.prezydium)
		response = self.client.post(
			reverse("sesja_edytuj", args=[self.sesja.id]),
			{
				"zapisz_sesje": "1",
				"data": "2026-04-06",
				"czas": "13:45",
				"opis": "Nowy opis sesji",
				"status": "aktywna",
			},
		)

		self.assertEqual(response.status_code, 302)
		self.sesja.refresh_from_db()
		lokalna_data = timezone.localtime(self.sesja.data)
		self.assertEqual(lokalna_data.date().isoformat(), "2026-04-06")
		self.assertEqual(lokalna_data.strftime("%H:%M"), "13:45")
		self.assertEqual(self.sesja.opis, "Nowy opis sesji")
		self.assertTrue(self.sesja.aktywna)

	def test_deactivating_point_removes_it_from_active_api(self):
		self.client.force_login(self.prezydium)
		response = self.client.post(reverse("ustaw_punkt_aktywny", args=[self.punkt.id]))

		self.assertEqual(response.status_code, 302)
		self.punkt.refresh_from_db()
		self.assertFalse(self.punkt.aktywny)

		api_response = self.client.get(reverse("api_aktywny_punkt", args=[self.sesja.id]))
		self.assertEqual(api_response.status_code, 200)
		self.assertFalse(api_response.json()["aktywny"])

	def test_deleting_point_removes_it_from_session(self):
		self.client.force_login(self.prezydium)
		response = self.client.post(reverse("usun_punkt_obrad", args=[self.punkt.id]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(PunktObrad.objects.filter(id=self.punkt.id).exists())

	def test_active_point_api_returns_formatted_safe_description_html(self):
		self.punkt.opis = "**Wazne**\n*kursywa*\n__podkreslenie__\n- pierwszy\n- drugi\n<script>alert(1)</script>"
		self.punkt.save(update_fields=["opis"])

		self.client.force_login(self.prezydium)
		response = self.client.get(reverse("api_aktywny_punkt", args=[self.sesja.id]))

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		html = payload.get("opis_html", "")
		self.assertIn("<strong>Wazne</strong>", html)
		self.assertIn("<em>kursywa</em>", html)
		self.assertIn("<u>podkreslenie</u>", html)
		self.assertIn("<ul>", html)
		self.assertIn("<li>pierwszy</li>", html)
		self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

	def test_session_edit_template_renders_formatted_description(self):
		self.punkt.opis = "**Wazne** i *kursywa*"
		self.punkt.save(update_fields=["opis"])

		self.client.force_login(self.prezydium)
		response = self.client.get(reverse("sesja_edytuj", args=[self.sesja.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "<strong>Wazne</strong>")
		self.assertContains(response, "<em>kursywa</em>")

	def test_add_point_modal_can_create_first_voting(self):
		self.client.force_login(self.prezydium)
		response = self.client.post(
			reverse("sesja_edytuj", args=[self.sesja.id]),
			{
				"dodaj_punkt": "1",
				"tytul": "Punkt z głosowaniem",
				"opis": "Opis punktu",
				"dodaj_glosowanie_nowy_punkt": "on",
				"nowe_glosowanie_typ": "zwykle",
				"nowe_glosowanie_nazwa": "Głosowanie do punktu",
				"nowe_glosowanie_jawnosc": "jawne",
				"nowe_glosowanie_wiekszosc": "zwykla",
				"nowe_glosowanie_liczba_uprawnionych": "9",
			},
		)

		self.assertEqual(response.status_code, 302)
		punkt = PunktObrad.objects.get(sesja=self.sesja, tytul="Punkt z głosowaniem")
		glosowanie = Glosowanie.objects.get(punkt_obrad=punkt)
		self.assertEqual(glosowanie.nazwa, "Głosowanie do punktu")
		self.assertEqual(glosowanie.typ, "zwykle")
		self.assertEqual(glosowanie.jawnosc, "jawne")
		self.assertEqual(glosowanie.wiekszosc, "zwykla")
		self.assertEqual(glosowanie.liczba_uprawnionych, 9)


class Custom404PageTests(TestCase):
	@override_settings(DEBUG=False)
	def test_custom_404_page_is_rendered(self):
		response = self.client.get("/to-nie-istnieje/")

		self.assertEqual(response.status_code, 404)
		self.assertContains(response, "Nie znaleziono tej strony.", status_code=404)
		self.assertContains(response, "Przejdź do panelu", status_code=404)


class KomisjaManagementTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.admin = Uzytkownik.objects.create_user(
			username="admin_kom",
			password="test12345",
			rola="administrator",
			imie="Admin",
			nazwisko="Komisji",
		)
		cls.prezydium = Uzytkownik.objects.create_user(
			username="prez_kom",
			password="test12345",
			rola="prezydium",
			imie="Pola",
			nazwisko="Prezydium",
		)
		cls.przewodniczacy = Uzytkownik.objects.create_user(
			username="chair_kom",
			password="test12345",
			rola="radny",
			imie="Piotr",
			nazwisko="Przewodniczacy",
		)
		cls.czlonek = Uzytkownik.objects.create_user(
			username="member_kom",
			password="test12345",
			rola="radny",
			imie="Celina",
			nazwisko="Czlonek",
		)
		cls.nowy_radny = Uzytkownik.objects.create_user(
			username="new_kom",
			password="test12345",
			rola="radny",
			imie="Norbert",
			nazwisko="Nowy",
		)
		cls.drugi_radny = Uzytkownik.objects.create_user(
			username="new_kom_2",
			password="test12345",
			rola="radny",
			imie="Damian",
			nazwisko="Drugi",
		)
		cls.inny_przewodniczacy = Uzytkownik.objects.create_user(
			username="chair_kom2",
			password="test12345",
			rola="radny",
			imie="Irena",
			nazwisko="Inna",
		)

		cls.komisja = Komisja.objects.create(
			nazwa="Komisja Finansow",
			opis="Test",
			przewodniczacy=cls.przewodniczacy,
		)
		cls.komisja.czlonkowie.add(cls.przewodniczacy, cls.czlonek)

		cls.inna_komisja = Komisja.objects.create(
			nazwa="Komisja Oswiaty",
			przewodniczacy=cls.inny_przewodniczacy,
		)
		cls.inna_komisja.czlonkowie.add(cls.inny_przewodniczacy)

	def test_admin_can_create_komisja(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			reverse("komisja_utworz"),
			{
				"nazwa": "Komisja Zdrowia",
				"opis": "Nowa komisja",
				"przewodniczacy": str(self.czlonek.id),
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(Komisja.objects.filter(nazwa="Komisja Zdrowia").exists())
		nowa = Komisja.objects.get(nazwa="Komisja Zdrowia")
		self.assertEqual(nowa.przewodniczacy_id, self.czlonek.id)
		self.assertTrue(nowa.czlonkowie.filter(id=self.czlonek.id).exists())

	def test_chair_can_create_session_for_own_komisja(self):
		self.client.force_login(self.przewodniczacy)
		response = self.client.post(
			reverse("komisja_dodaj_sesje", args=[self.komisja.id]),
			{"nazwa": "Posiedzenie 1", "data": "2026-04-10T10:30", "aktywna": "on"},
		)

		self.assertEqual(response.status_code, 302)
		sesja = KomisjaSesja.objects.get(komisja=self.komisja, nazwa="Posiedzenie 1")
		self.assertTrue(sesja.aktywna)

	def test_chair_cannot_create_session_for_other_komisja(self):
		self.client.force_login(self.przewodniczacy)
		response = self.client.post(
			reverse("komisja_dodaj_sesje", args=[self.inna_komisja.id]),
			{"nazwa": "Niedozwolona sesja"},
		)

		self.assertEqual(response.status_code, 403)
		self.assertFalse(KomisjaSesja.objects.filter(komisja=self.inna_komisja, nazwa="Niedozwolona sesja").exists())

	def test_admin_can_create_komisja_with_member_list(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			reverse("komisja_utworz"),
			{
				"nazwa": "Komisja Infrastruktury",
				"opis": "Komisja testowa",
				"przewodniczacy": str(self.przewodniczacy.id),
				"czlonkowie": [str(self.czlonek.id), str(self.nowy_radny.id)],
			},
		)

		self.assertEqual(response.status_code, 302)
		nowa = Komisja.objects.get(nazwa="Komisja Infrastruktury")
		self.assertTrue(nowa.czlonkowie.filter(id=self.przewodniczacy.id).exists())
		self.assertTrue(nowa.czlonkowie.filter(id=self.czlonek.id).exists())
		self.assertTrue(nowa.czlonkowie.filter(id=self.nowy_radny.id).exists())

	def test_admin_can_add_and_remove_member(self):
		self.client.force_login(self.admin)
		add_response = self.client.post(
			reverse("komisja_dodaj_czlonka", args=[self.komisja.id]),
			{"radny_id": str(self.nowy_radny.id)},
		)
		self.assertEqual(add_response.status_code, 302)
		self.assertTrue(self.komisja.czlonkowie.filter(id=self.nowy_radny.id).exists())

		remove_response = self.client.post(
			reverse("komisja_usun_czlonka", args=[self.komisja.id, self.nowy_radny.id]),
		)
		self.assertEqual(remove_response.status_code, 302)
		self.assertFalse(self.komisja.czlonkowie.filter(id=self.nowy_radny.id).exists())

	def test_admin_can_add_multiple_members(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			reverse("komisja_dodaj_czlonka", args=[self.komisja.id]),
			{"radny_ids": [str(self.nowy_radny.id), str(self.drugi_radny.id)]},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(self.komisja.czlonkowie.filter(id=self.nowy_radny.id).exists())
		self.assertTrue(self.komisja.czlonkowie.filter(id=self.drugi_radny.id).exists())

	def test_admin_can_add_prezydium_and_admin_to_committee(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			reverse("komisja_dodaj_czlonka", args=[self.komisja.id]),
			{"radny_ids": [str(self.prezydium.id), str(self.admin.id)]},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(self.komisja.czlonkowie.filter(id=self.prezydium.id).exists())
		self.assertTrue(self.komisja.czlonkowie.filter(id=self.admin.id).exists())

	def test_regular_member_cannot_manage_members(self):
		self.client.force_login(self.czlonek)
		response = self.client.post(
			reverse("komisja_dodaj_czlonka", args=[self.komisja.id]),
			{"radny_id": str(self.nowy_radny.id)},
		)

		self.assertEqual(response.status_code, 403)

	def test_commission_request_is_visible_in_prezydium_inbox(self):
		self.client.force_login(self.czlonek)
		create_response = self.client.post(
			reverse("komisja_wnioski", args=[self.komisja.id]),
			{"typ": "wniosek", "tresc": "Prosba o analizę."},
		)
		self.assertEqual(create_response.status_code, 302)

		wniosek = KomisjaWniosek.objects.get(komisja=self.komisja)
		self.assertFalse(wniosek.wyslany_do_rady)

		self.client.force_login(self.prezydium)
		inbox_response = self.client.get(reverse("komisja_skrzynka_rady"))
		self.assertEqual(inbox_response.status_code, 200)
		self.assertContains(inbox_response, "Prosba o analizę.")


class KomisjaSessionEditingTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.admin = Uzytkownik.objects.create_user(
			username="admin_kom_sesja",
			password="test12345",
			rola="administrator",
			imie="Ala",
			nazwisko="Admin",
		)
		cls.chair = Uzytkownik.objects.create_user(
			username="chair_kom_sesja",
			password="test12345",
			rola="radny",
			imie="Cezary",
			nazwisko="Chair",
		)
		cls.member = Uzytkownik.objects.create_user(
			username="member_kom_sesja",
			password="test12345",
			rola="radny",
			imie="Marta",
			nazwisko="Member",
		)
		cls.other_chair = Uzytkownik.objects.create_user(
			username="chair_kom_sesja_2",
			password="test12345",
			rola="radny",
			imie="Olga",
			nazwisko="Other",
		)

		cls.komisja = Komisja.objects.create(
			nazwa="Komisja IT",
			przewodniczacy=cls.chair,
		)
		cls.komisja.czlonkowie.add(cls.chair, cls.member)
		cls.sesja = KomisjaSesja.objects.create(
			komisja=cls.komisja,
			nazwa="Posiedzenie IT",
			data=timezone.now(),
		)

		cls.inna_komisja = Komisja.objects.create(
			nazwa="Komisja GEO",
			przewodniczacy=cls.other_chair,
		)
		cls.inna_komisja.czlonkowie.add(cls.other_chair)
		cls.inna_sesja = KomisjaSesja.objects.create(
			komisja=cls.inna_komisja,
			nazwa="Posiedzenie GEO",
			data=timezone.now(),
		)

	def test_chair_can_add_point_and_voting(self):
		self.client.force_login(self.chair)
		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{"dodaj_punkt": "1", "numer": 1, "tytul": "Budżet", "opis": "Omówienie"},
		)
		self.assertEqual(response.status_code, 302)

		punkt = KomisjaPunktObrad.objects.get(sesja=self.sesja, tytul="Budżet")

		response2 = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{
				"dodaj_glosowanie": "1",
				"punkt_id": str(punkt.id),
				"nazwa": "Głosowanie budżet",
				"jawnosc": "jawne",
				"wiekszosc": "zwykla",
				"liczba_uprawnionych": "5",
			},
		)
		self.assertEqual(response2.status_code, 302)
		self.assertTrue(KomisjaGlosowanie.objects.filter(punkt_obrad=punkt, nazwa="Głosowanie budżet").exists())

	def test_chair_can_edit_session_meta(self):
		self.client.force_login(self.chair)
		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{"zapisz_sesje": "1", "nazwa": "Posiedzenie IT - aktualizacja", "data": "2026-04-08T11:15", "status": "aktywna"},
		)
		self.assertEqual(response.status_code, 302)
		self.sesja.refresh_from_db()
		self.assertEqual(self.sesja.nazwa, "Posiedzenie IT - aktualizacja")
		self.assertTrue(self.sesja.aktywna)

	def test_member_cannot_edit_committee_session(self):
		self.client.force_login(self.member)
		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{"dodaj_punkt": "1", "numer": 1, "tytul": "Niedozwolone", "opis": "X"},
		)
		self.assertEqual(response.status_code, 403)

	def test_chair_can_add_point_without_numer_in_post(self):
		self.client.force_login(self.chair)
		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{"dodaj_punkt": "1", "tytul": "Nowy punkt", "opis": "Opis"},
		)

		self.assertEqual(response.status_code, 302)
		punkt = KomisjaPunktObrad.objects.get(sesja=self.sesja, tytul="Nowy punkt")
		self.assertEqual(punkt.numer, 1)

	def test_chair_can_add_point_with_initial_voting_in_one_submit(self):
		self.client.force_login(self.chair)
		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{
				"dodaj_punkt": "1",
				"tytul": "Punkt z głosowaniem",
				"opis": "Opis punktu",
				"dodaj_glosowanie_nowy_punkt": "on",
				"nowe_glosowanie_nazwa": "Głosowanie do punktu",
				"nowe_glosowanie_jawnosc": "jawne",
				"nowe_glosowanie_wiekszosc": "zwykla",
				"nowe_glosowanie_liczba_uprawnionych": "5",
			},
		)

		self.assertEqual(response.status_code, 302)
		punkt = KomisjaPunktObrad.objects.get(sesja=self.sesja, tytul="Punkt z głosowaniem")
		glosowanie = KomisjaGlosowanie.objects.get(punkt_obrad=punkt)
		self.assertEqual(glosowanie.nazwa, "Głosowanie do punktu")
		self.assertEqual(glosowanie.jawnosc, "jawne")
		self.assertEqual(glosowanie.wiekszosc, "zwykla")
		self.assertEqual(glosowanie.liczba_uprawnionych, 5)

	def test_chair_cannot_edit_other_committee_session(self):
		self.client.force_login(self.chair)
		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.inna_komisja.id, self.inna_sesja.id]),
			{"dodaj_punkt": "1", "numer": 1, "tytul": "Niedozwolone", "opis": "X"},
		)
		self.assertEqual(response.status_code, 403)

	def test_active_point_is_persisted_on_komisja_session(self):
		self.client.force_login(self.chair)
		punkt = KomisjaPunktObrad.objects.create(
			sesja=self.sesja,
			numer=1,
			tytul="Punkt aktywny",
		)

		response = self.client.post(
			reverse("komisja_sesja_edytuj", args=[self.komisja.id, self.sesja.id]),
			{"ustaw_punkt_aktywny": "1", "punkt_id": str(punkt.id)},
		)
		self.assertEqual(response.status_code, 302)

		self.sesja.refresh_from_db()
		punkt.refresh_from_db()
		self.assertEqual(self.sesja.aktywny_punkt_id, punkt.id)
		self.assertTrue(punkt.aktywny)

		api_response = self.client.get(reverse("api_komisja_aktywny_punkt", args=[self.sesja.id]))
		self.assertEqual(api_response.status_code, 200)
		self.assertEqual(api_response.json().get("numer"), 1)
		self.assertEqual(api_response.json().get("tytul"), "Punkt aktywny")


class KomisjaVotingPermissionsTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.chair = Uzytkownik.objects.create_user(
			username="chair_vote_kom",
			password="test12345",
			rola="radny",
			imie="Karol",
			nazwisko="Chair",
		)
		cls.member = Uzytkownik.objects.create_user(
			username="member_vote_kom",
			password="test12345",
			rola="radny",
			imie="Maja",
			nazwisko="Member",
		)
		cls.outsider = Uzytkownik.objects.create_user(
			username="outsider_vote_kom",
			password="test12345",
			rola="radny",
			imie="Ola",
			nazwisko="Outside",
		)
		cls.admin = Uzytkownik.objects.create_user(
			username="admin_vote_kom",
			password="test12345",
			rola="administrator",
			imie="Ada",
			nazwisko="Admin",
		)

		cls.komisja = Komisja.objects.create(
			nazwa="Komisja Budzetu",
			przewodniczacy=cls.chair,
		)
		cls.komisja.czlonkowie.add(cls.chair, cls.member)
		cls.sesja = KomisjaSesja.objects.create(
			komisja=cls.komisja,
			nazwa="Posiedzenie Budzetu",
			data=timezone.now(),
		)
		cls.punkt = KomisjaPunktObrad.objects.create(
			sesja=cls.sesja,
			numer=1,
			tytul="Plan finansowy",
			aktywny=True,
		)
		cls.glosowanie = KomisjaGlosowanie.objects.create(
			punkt_obrad=cls.punkt,
			nazwa="Głosowanie budżetowe",
			otwarte=True,
			jawnosc="jawne",
		)

	def test_member_can_vote_in_committee(self):
		self.client.force_login(self.member)
		response = self.client.post(
			reverse("komisja_oddaj_glos", args=[self.glosowanie.id]),
			{"glos": "za"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(
			KomisjaGlos.objects.filter(
				glosowanie=self.glosowanie,
				uzytkownik=self.member,
				glos="za",
			).exists()
		)

	def test_outsider_cannot_vote_in_committee(self):
		self.client.force_login(self.outsider)
		response = self.client.post(
			reverse("komisja_oddaj_glos", args=[self.glosowanie.id]),
			{"glos": "za"},
		)

		self.assertEqual(response.status_code, 403)
		self.assertFalse(
			KomisjaGlos.objects.filter(
				glosowanie=self.glosowanie,
				uzytkownik=self.outsider,
			).exists()
		)

	def test_admin_cannot_vote_if_not_member(self):
		self.client.force_login(self.admin)
		response = self.client.post(
			reverse("komisja_oddaj_glos", args=[self.glosowanie.id]),
			{"glos": "przeciw"},
		)

		self.assertEqual(response.status_code, 403)
		self.assertFalse(
			KomisjaGlos.objects.filter(
				glosowanie=self.glosowanie,
				uzytkownik=self.admin,
			).exists()
		)

	def test_chair_can_toggle_committee_voting(self):
		self.client.force_login(self.chair)
		response = self.client.post(reverse("komisja_toggle_glosowanie", args=[self.glosowanie.id]))

		self.assertEqual(response.status_code, 302)
		self.glosowanie.refresh_from_db()
		self.assertFalse(self.glosowanie.otwarte)

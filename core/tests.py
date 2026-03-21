from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Uzytkownik
from core.models import Sesja, PunktObrad, Glosowanie, Obecnosc


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

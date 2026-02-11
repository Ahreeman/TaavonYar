from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Individual, Shareholder


User = get_user_model()


class RegistrationFlowTests(TestCase):
    def test_register_creates_individual_and_default_shareholder(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "ali",
                "password1": "S3curePass123",
                "password2": "S3curePass123",
                "full_name": "Ali Rezaei",
                "national_number": "1234567890",
                "phone_number": "09121111111",
                "address": "Village 1",
                "post_id": "9876543210",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="ali")
        individual = Individual.objects.get(user=user)
        shareholder = Shareholder.objects.get(individual=individual)

        self.assertEqual(individual.full_name, "Ali Rezaei")
        self.assertTrue(shareholder.shareholder_id.startswith("SH-"))

    def test_newly_registered_user_can_access_shareholder_dashboard(self):
        user = User.objects.create_user(username="sara", password="S3curePass123")
        ind = Individual.objects.create(
            user=user,
            full_name="Sara Ahmadi",
            national_number="1111111111",
        )
        Shareholder.objects.create(
            individual=ind,
            shareholder_id="SH-TEST-SARA",
            bank_account_number="PENDING",
        )

        self.client.login(username="sara", password="S3curePass123")
        response = self.client.get(reverse("accounts:dashboard"))

        self.assertRedirects(response, reverse("shares:shareholder_dashboard"))


class LogoutFlowTests(TestCase):
    def test_logout_page_redirects_to_login(self):
        user = User.objects.create_user(username="reza", password="S3curePass123")
        self.client.login(username="reza", password="S3curePass123")

        response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You are logged out")
        self.assertContains(response, reverse("accounts:login"))


def test_register_rejects_duplicate_national_number(self):
    user = User.objects.create_user(username="existing", password="S3curePass123")
    Individual.objects.create(
        user=user,
        full_name="Existing User",
        national_number="1234567890",
    )

    response = self.client.post(
        reverse("accounts:register"),
        {
            "username": "newuser",
            "password1": "S3curePass123",
            "password2": "S3curePass123",
            "full_name": "New User",
            "national_number": "1234567890",
        },
    )

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "already registered")


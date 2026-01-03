from django.conf import settings
from django.db import models

# Create your models here.

class Individual(models.Model):
    """Basic person identity record.
    Linked to Django auth User so we can authenticate normally."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="individual",
    )

    full_name = models.CharField(max_length=200)
    birth_date = models.DateField(null=True, blank=True)

    phone_number = models.CharField(max_length=30, blank=True)
    national_number = models.CharField(max_length=15, unique=True)

    address = models.TextField(blank=True)
    post_id = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.national_number})"
    

class Shareholder(models.Model):
    """Shareholder profile info (only exists if this individual is a shareholder)."""
    
    individual = models.OneToOneField(
        Individual,
        on_delete=models.CASCADE,
        related_name="shareholder_profile",
    )

    shareholder_id = models.CharField(max_length=50, unique=True)
    bank_account_number = models.CharField(max_length=80)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Shareholder {self.shareholder_id} - {self.individual.full_name}"


class BoardMember(models.Model):
    """
    Board/manager profile info (only exists if this individual is a board member).
    A user can be board member in exactly ONE cooperative.
    """
    class AuthorityStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    individual = models.OneToOneField(
        Individual,
        on_delete=models.CASCADE,
        related_name="board_profile",
    )

    # Cooperative model is in coops app; we reference it by string to avoid import cycles
    cooperative = models.OneToOneField(
        "coops.Cooperative",
        on_delete=models.PROTECT,
        related_name="board_member",
    )

    boardmember_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20,
        choices=AuthorityStatus.choices,
        default=AuthorityStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"BoardMember {self.boardmember_id} - {self.individual.full_name}"
from django.conf import settings
from django.db import models


class ShareHolding(models.Model):
    cooperative = models.ForeignKey("coops.Cooperative", on_delete=models.CASCADE, related_name="holdings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="share_holdings")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("cooperative", "user")

    def __str__(self) -> str:
        return f"{self.user} - {self.cooperative.name}: {self.quantity}"


class ShareListing(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SOLD_OUT = "SOLD_OUT", "Sold out"
        CANCELED = "CANCELED", "Canceled"

    cooperative = models.ForeignKey("coops.Cooperative", on_delete=models.CASCADE, related_name="listings")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="share_listings")

    quantity_available = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Snapshot for audit, still must equal coop.price_per_share at creation time
    price_per_share = models.PositiveBigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.cooperative.name} listing by {self.seller} ({self.quantity_available})"


class ShareTrade(models.Model):
    cooperative = models.ForeignKey("coops.Cooperative", on_delete=models.CASCADE, related_name="trades")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="share_buys")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="share_sells",
    )

    quantity = models.PositiveIntegerField()
    price_per_share = models.PositiveBigIntegerField()
    total_price = models.PositiveBigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        who = "COOP" if self.seller is None else str(self.seller)
        return f"{who} -> {self.buyer} {self.quantity} @ {self.price_per_share}"

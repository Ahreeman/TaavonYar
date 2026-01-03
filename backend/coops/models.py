from django.db import models

class Cooperative(models.Model):
    name = models.CharField(max_length=200, unique=True)
    village = models.CharField(max_length=200, blank=True)

    description = models.TextField(blank=True)

    # Share policy (Tooman)
    price_per_share = models.PositiveBigIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)

    # Optional presentation fields
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

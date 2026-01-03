from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        DONE = "DONE", "Done"
        CANCELED = "CANCELED", "Canceled"

    cooperative = models.ForeignKey(
        "coops.Cooperative",
        on_delete=models.CASCADE,
        related_name="projects",
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="projects/", null=True, blank=True)

    goal_amount = models.PositiveBigIntegerField()  # Tooman
    shares_to_distribute = models.PositiveIntegerField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_fully_funded = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.cooperative.name})"

    @property
    def total_contributed(self) -> int:
        agg = self.contributions.aggregate(total=models.Sum("amount"))
        return int(agg["total"] or 0)


class Contribution(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="contributions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contributions")

    amount = models.PositiveBigIntegerField()  # Tooman
    created_at = models.DateTimeField(auto_now_add=True)

    # set when project is DONE (distribution)
    allocated_shares = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user} -> {self.project} : {self.amount} Tooman"

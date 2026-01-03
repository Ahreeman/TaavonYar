from django.contrib import admin
from .models import Project, Contribution


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "cooperative", "status", "goal_amount", "shares_to_distribute", "is_fully_funded", "created_at")
    list_filter = ("status", "is_fully_funded", "created_at")
    search_fields = ("title", "cooperative__name")


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "amount", "allocated_shares", "created_at")
    list_filter = ("created_at",)
    search_fields = ("project__title", "user__username")

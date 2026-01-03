from django.contrib import admin
from .models import Cooperative

@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ("name", "village", "price_per_share", "total_shares", "created_at")
    search_fields = ("name", "village")
    list_filter = ("created_at",)
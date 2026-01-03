from django.contrib import admin
from .models import ShareHolding, ShareListing, ShareTrade


@admin.register(ShareHolding)
class ShareHoldingAdmin(admin.ModelAdmin):
    list_display = ("cooperative", "user", "quantity")
    search_fields = ("cooperative__name", "user__username")


@admin.register(ShareListing)
class ShareListingAdmin(admin.ModelAdmin):
    list_display = ("cooperative", "seller", "quantity_available", "price_per_share", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("cooperative__name", "seller__username")


@admin.register(ShareTrade)
class ShareTradeAdmin(admin.ModelAdmin):
    list_display = ("cooperative", "buyer", "seller", "quantity", "price_per_share", "total_price", "created_at")
    list_filter = ("created_at",)
    search_fields = ("cooperative__name", "buyer__username", "seller__username")

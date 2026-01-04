from django.urls import path
from .views import shareholder_dashboard, marketplace, create_listing, buy_listing, buy_primary, my_listings, cancel_listing, my_trades

app_name = "shares"

urlpatterns = [
    path("dashboard/", shareholder_dashboard, name="shareholder_dashboard"),

    path("marketplace/", marketplace, name="marketplace"),
    path("marketplace/list/", create_listing, name="create_listing"),
    path("marketplace/buy/<int:listing_id>/", buy_listing, name="buy_listing"),

    path("primary/buy/", buy_primary, name="buy_primary"),

    path("my-listings/", my_listings, name="my_listings"),
    path("my-listings/<int:listing_id>/cancel/", cancel_listing, name="cancel_listing"),
    path("my-trades/", my_trades, name="my_trades"),
]

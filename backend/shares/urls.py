from django.urls import path
from .views import *

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
    path("marketplace/buy/", buy_marketplace, name="buy_marketplace"),
    path("export/holdings/", export_my_holdings_csv, name="export_my_holdings_csv"),
    path("export/contributions/", export_my_contributions_csv, name="export_my_contributions_csv"),
    path("export/trades/", export_my_trade_logs_csv, name="export_my_trade_logs_csv"),

]

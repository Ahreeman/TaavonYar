from django.urls import path
from .views import shareholder_dashboard, marketplace, create_listing, buy_listing, buy_primary

urlpatterns = [
    path("dashboard/", shareholder_dashboard, name="shareholder_dashboard"),

    path("marketplace/", marketplace, name="marketplace"),
    path("marketplace/list/", create_listing, name="create_listing"),
    path("marketplace/buy/<int:listing_id>/", buy_listing, name="buy_listing"),

    path("primary/buy/", buy_primary, name="buy_primary"),
]

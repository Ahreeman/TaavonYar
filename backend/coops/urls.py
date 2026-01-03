from django.urls import path
from .views import coop_list, coop_detail

urlpatterns = [
    path("", coop_list, name="coop_list"),
    path("<int:coop_id>/", coop_detail, name="coop_detail"),

]

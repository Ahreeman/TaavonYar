from django.urls import path
from .views import coop_list

urlpatterns = [
    path("", coop_list, name="coop_list"),
]

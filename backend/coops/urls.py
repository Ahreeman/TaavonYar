from django.urls import path
from .views import coop_list, coop_detail, board_coop_edit


app_name = "coops"


urlpatterns = [
    path("", coop_list, name="coop_list"),
    path("<int:coop_id>/", coop_detail, name="coop_detail"),
    path("board/edit/", board_coop_edit, name="board_coop_edit"),


]

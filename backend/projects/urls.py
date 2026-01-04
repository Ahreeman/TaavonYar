from django.urls import path
from .views import project_list, project_detail, contribute, board_dashboard, mark_done

urlpatterns = [
    path("", project_list, name="project_list"),
    path("<int:project_id>/", project_detail, name="project_detail"),
    path("<int:project_id>/contribute/", contribute, name="project_contribute"),

    path("board/", board_dashboard, name="board_dashboard"),
    path("<int:project_id>/mark-done/", mark_done, name="project_mark_done"),
]

from django.urls import path
from .views import (
    project_list, project_detail, contribute,
    board_dashboard, mark_done,
    board_project_create, board_project_edit,
)

app_name = "projects"


urlpatterns = [
    path("", project_list, name="project_list"),
    path("<int:project_id>/", project_detail, name="project_detail"),
    path("<int:project_id>/contribute/", contribute, name="project_contribute"),

    path("board/", board_dashboard, name="board_dashboard"),
    path("board/create/", board_project_create, name="board_project_create"),
    path("board/<int:project_id>/edit/", board_project_edit, name="board_project_edit"),
    path("<int:project_id>/mark-done/", mark_done, name="project_mark_done"),
]

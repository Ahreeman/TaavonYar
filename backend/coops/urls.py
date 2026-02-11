from django.urls import path
from .views import *


app_name = "coops"


urlpatterns = [
    path("", coop_list, name="coop_list"),
    path("<int:coop_id>/", coop_detail, name="coop_detail"),
    path("board/edit/", board_coop_edit, name="board_coop_edit"),
    path("board/export/shareholders/", export_shareholder_info_csv, name="export_shareholders_csv"),
    path("board/export/trades/", export_share_purchase_logs_csv, name="export_trades_csv"),
    path("board/export/summary/", export_coop_share_summary_csv, name="export_summary_csv"),


]

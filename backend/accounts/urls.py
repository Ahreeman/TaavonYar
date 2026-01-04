from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dashboard, profile, switch_mode, choose_dashboard

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("profile/", profile, name="profile"),
    path("dashboard/", dashboard, name="dashboard"),
    path("choose/", choose_dashboard, name="choose_dashboard"),
    path("switch/<str:mode>/", switch_mode, name="switch_mode"),
]

from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    choose_dashboard,
    dashboard,
    logout_then_redirect,
    profile,
    register,
    switch_mode,
)

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", logout_then_redirect, name="logout"),
    path("register/", register, name="register"),
    path("profile/", profile, name="profile"),
    path("dashboard/", dashboard, name="dashboard"),
    path("choose/", choose_dashboard, name="choose_dashboard"),
    path("switch/<str:mode>/", switch_mode, name="switch_mode"),
]

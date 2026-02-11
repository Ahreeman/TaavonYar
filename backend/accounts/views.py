from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

from django.db import transaction
from .forms import RegistrationForm


from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


import uuid

from .models import Individual, Shareholder


@login_required
def profile(request):
    if hasattr(request.user, "individual"):
        return redirect("accounts:dashboard")

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        national_number = (request.POST.get("national_number") or "").strip()
        phone_number = (request.POST.get("phone_number") or "").strip()
        address = (request.POST.get("address") or "").strip()
        post_id = (request.POST.get("post_id") or "").strip()

        if full_name and national_number:
            Individual.objects.create(
                user=request.user,
                full_name=full_name,
                national_number=national_number,
                phone_number=phone_number,
                address=address,
                post_id=post_id,
            )
            return redirect("accounts:dashboard")

    return render(request, "accounts/profile.html")


def _role_flags(user):
    if not hasattr(user, "individual"):
        return False, False
    ind = user.individual
    is_board = hasattr(ind, "board_profile")
    is_shareholder = hasattr(ind, "shareholder_profile")
    return is_board, is_shareholder


@login_required
def switch_mode(request, mode: str):
    """
    Save preferred dashboard mode in session.
    mode: 'board' or 'shareholder'
    """
    is_board, is_shareholder = _role_flags(request.user)

    if mode == "board" and is_board:
        request.session["dashboard_mode"] = "board"
        return redirect("projects:board_dashboard")  # IMPORTANT: return

    if mode == "shareholder" and is_shareholder:
        request.session["dashboard_mode"] = "shareholder"
        return redirect("shares:shareholder_dashboard")

    # invalid or user doesn't have the role
    return redirect("accounts:dashboard")


@login_required
def dashboard(request):
    # Require Individual
    if not hasattr(request.user, "individual"):
        return redirect("accounts:profile")

    is_board, is_shareholder = _role_flags(request.user)

    if not is_board and not is_shareholder:
        return redirect("shares:shareholder_dashboard")

    if is_board and not is_shareholder:
        request.session["dashboard_mode"] = "board"
        return redirect("projects:board_dashboard")  # IMPORTANT: return

    if is_shareholder and not is_board:
        request.session["dashboard_mode"] = "shareholder"
        return redirect("shares:shareholder_dashboard")

    preferred = request.session.get("dashboard_mode")
    if preferred == "board":
        return redirect("projects:board_dashboard")
    if preferred == "shareholder":
        return redirect("shares:shareholder_dashboard")

    return render(request, "accounts/dashboard_switch.html")


@login_required
def choose_dashboard(request):
    if not hasattr(request.user, "individual"):
        return redirect("accounts:profile")

    is_board, is_shareholder = _role_flags(request.user)

    if is_board and not is_shareholder:
        request.session["dashboard_mode"] = "board"
        return redirect("projects:board_dashboard")  # IMPORTANT: return

    if is_shareholder and not is_board:
        request.session["dashboard_mode"] = "shareholder"
        return redirect("shares:shareholder_dashboard")

    request.session.pop("dashboard_mode", None)
    return render(request, "accounts/dashboard_switch.html")


def _new_shareholder_id() -> str:
    return f"SH-{uuid.uuid4().hex[:12].upper()}"


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()

            individual = Individual.objects.create(
                user=user,
                full_name=form.cleaned_data["full_name"],
                national_number=form.cleaned_data["national_number"],
                phone_number=form.cleaned_data.get("phone_number", ""),
                address=form.cleaned_data.get("address", ""),
                post_id=form.cleaned_data.get("post_id", ""),
            )

            Shareholder.objects.create(
                individual=individual,
                shareholder_id=_new_shareholder_id(),
                bank_account_number="PENDING",
            )

        messages.success(request, "Account created. Please log in.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})



@require_http_methods(["GET", "POST"])
def logout_then_redirect(request):
    logout(request)
    return render(request, "accounts/logged_out.html")

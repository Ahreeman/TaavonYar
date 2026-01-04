from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Individual


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
        return redirect("board_dashboard")

    if mode == "shareholder" and is_shareholder:
        request.session["dashboard_mode"] = "shareholder"
        return redirect("shareholder_dashboard")

    # invalid or user doesn't have the role
    return redirect("accounts:dashboard")


@login_required
def dashboard(request):
    # Require Individual
    if not hasattr(request.user, "individual"):
        return redirect("accounts:profile")

    is_board, is_shareholder = _role_flags(request.user)

    # If user has neither role profile, send them to shareholder dashboard anyway
    # (they can still browse; later we'll build role-creation UI)
    if not is_board and not is_shareholder:
        return redirect("shareholder_dashboard")

    # If user has only one role, go directly
    if is_board and not is_shareholder:
        request.session["dashboard_mode"] = "board"
        return redirect("board_dashboard")

    if is_shareholder and not is_board:
        request.session["dashboard_mode"] = "shareholder"
        return redirect("shareholder_dashboard")

    # User has BOTH roles
    preferred = request.session.get("dashboard_mode")
    if preferred == "board":
        return redirect("board_dashboard")
    if preferred == "shareholder":
        return redirect("shareholder_dashboard")

    # No preference yet -> show switch page
    return render(request, "accounts/dashboard_switch.html")

@login_required
def choose_dashboard(request):
    if not hasattr(request.user, "individual"):
        return redirect("accounts:profile")

    is_board, is_shareholder = _role_flags(request.user)

    # If only one role, just go there
    if is_board and not is_shareholder:
        request.session["dashboard_mode"] = "board"
        return redirect("board_dashboard")

    if is_shareholder and not is_board:
        request.session["dashboard_mode"] = "shareholder"
        return redirect("shareholder_dashboard")

    # If both roles -> CLEAR preference so the chooser is shown
    request.session.pop("dashboard_mode", None)
    return render(request, "accounts/dashboard_switch.html")


from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count
from .models import Cooperative
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import BoardMember


def coop_list(request):
    coops = Cooperative.objects.order_by("name")
    return render(request, "coops/coop_list.html", {"coops": coops})


def coop_detail(request, coop_id: int):
    coop = get_object_or_404(Cooperative, id=coop_id)

    projects = coop.projects.order_by("-created_at")
    active_projects = projects.filter(status="ACTIVE")
    done_projects = projects.filter(status="DONE")

    # Basic stats (safe even if empty)
    total_contributions = coop.projects.aggregate(
        total=Sum("contributions__amount")
    )["total"] or 0

    # Approx shareholder count = count of holdings with quantity > 0
    shareholder_count = coop.holdings.filter(quantity__gt=0).count()

    return render(
        request,
        "coops/coop_detail.html",
        {
            "coop": coop,
            "active_projects": active_projects,
            "done_projects": done_projects,
            "total_contributions": total_contributions,
            "shareholder_count": shareholder_count,
        },
    )



@login_required
def board_coop_edit(request):
    # Must be accepted board member
    if not hasattr(request.user, "individual") or not hasattr(request.user.individual, "board_profile"):
        messages.error(request, "You are not a board member.")
        return redirect("accounts:dashboard")

    board: BoardMember = request.user.individual.board_profile
    if board.status != BoardMember.AuthorityStatus.ACCEPTED:
        messages.error(request, "Your board membership is not accepted by authorities.")
        return redirect("accounts:dashboard")

    coop = board.cooperative

    if request.method == "POST":
        coop.name = (request.POST.get("name") or "").strip()
        coop.village = (request.POST.get("village") or "").strip()
        coop.description = (request.POST.get("description") or "").strip()
        coop.phone = (request.POST.get("phone") or "").strip()
        coop.website = (request.POST.get("website") or "").strip()

        # share settings
        coop.price_per_share = int(request.POST.get("price_per_share") or coop.price_per_share)
        coop.total_shares = int(request.POST.get("total_shares") or coop.total_shares)
        coop.available_primary_shares = int(request.POST.get("available_primary_shares") or coop.available_primary_shares)

        # image upload (optional)
        if "image" in request.FILES:
            coop.image = request.FILES["image"]

        coop.save()
        messages.success(request, "Cooperative profile updated.")
        return redirect("coops:board_coop_edit")

    return render(request, "coops/board_coop_edit.html", {"coop": coop})

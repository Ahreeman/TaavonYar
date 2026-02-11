from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count
from .models import Cooperative
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import BoardMember
from django.http import HttpResponse, Http404
import csv
from shares.models import ShareHolding
from shares.models import ShareTrade


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


def _require_accepted_board(user) -> BoardMember:
    if not hasattr(user, "individual") or not hasattr(user.individual, "board_profile"):
        raise PermissionError("Not a board member")
    board = user.individual.board_profile
    if board.status != BoardMember.AuthorityStatus.ACCEPTED:
        raise PermissionError("Board membership not accepted")
    return board



@login_required
def export_shareholder_info_csv(request):
    board = _require_accepted_board(request.user)
    coop = board.cooperative

    holdings = (
        ShareHolding.objects
        .select_related("user__individual", "cooperative")
        .filter(cooperative=coop, quantity__gt=0)
        .order_by("-quantity")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{coop.id}_shareholder_info.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "full_name", "national_number", "phone_number", "address", "post_id",
        "shares", "price_per_share", "share_worth_tooman"
    ])

    for h in holdings:
        ind = getattr(h.user, "individual", None)
        if not ind:
            continue
        worth = h.quantity * coop.price_per_share
        writer.writerow([
            ind.full_name,
            ind.national_number,
            ind.phone_number,
            ind.address,
            ind.post_id,
            h.quantity,
            coop.price_per_share,
            worth,
        ])

    return response



@login_required
def export_share_purchase_logs_csv(request):
    board = _require_accepted_board(request.user)
    coop = board.cooperative

    trades = (
        ShareTrade.objects
        .select_related("buyer__individual", "seller__individual")
        .filter(cooperative=coop)
        .order_by("-created_at")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{coop.id}_share_purchase_logs.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "created_at", "buyer_name", "buyer_national_id",
        "seller_name", "seller_national_id",
        "quantity", "price_per_share", "total_price"
    ])

    for t in trades:
        buyer_ind = getattr(t.buyer, "individual", None)
        seller_ind = getattr(t.seller, "individual", None) if t.seller else None

        writer.writerow([
            t.created_at.isoformat(),
            buyer_ind.full_name if buyer_ind else t.buyer.username,
            buyer_ind.national_number if buyer_ind else "",
            seller_ind.full_name if seller_ind else ("COOP_PRIMARY" if t.seller is None else str(t.seller)),
            seller_ind.national_number if seller_ind else "",
            t.quantity,
            t.price_per_share,
            t.total_price,
        ])

    return response


@login_required
def export_coop_share_summary_csv(request):
    board = _require_accepted_board(request.user)
    coop = board.cooperative

    holdings = (
        ShareHolding.objects
        .select_related("user__individual")
        .filter(cooperative=coop, quantity__gt=0)
        .order_by("-quantity")
    )

    total_held = holdings.aggregate(total=Sum("quantity"))["total"] or 0
    total_value = total_held * coop.price_per_share

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{coop.id}_coop_share_summary.csv"'
    writer = csv.writer(response)

    # header/meta rows
    writer.writerow(["cooperative_name", coop.name])
    writer.writerow(["price_per_share", coop.price_per_share])
    writer.writerow(["total_shares_defined", coop.total_shares])
    writer.writerow(["available_primary_shares", coop.available_primary_shares])
    writer.writerow(["total_held_shares", total_held])
    writer.writerow(["total_held_value_tooman", total_value])
    writer.writerow([])

    # detail section
    writer.writerow(["shareholder_name", "national_number", "shares", "percentage_of_held_shares"])
    for h in holdings:
        ind = getattr(h.user, "individual", None)
        if not ind:
            continue
        pct = (h.quantity / total_held * 100) if total_held else 0
        writer.writerow([ind.full_name, ind.national_number, h.quantity, round(pct, 2)])

    return response
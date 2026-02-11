from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib import messages
from coops.models import Cooperative
from projects.models import Contribution
from .models import ShareHolding, ShareListing, ShareTrade
from .services import (
    create_listing as svc_create_listing,
    buy_from_listing,
    buy_primary_shares_from_coop,
    buy_from_marketplace,
)
from django.db import models
import csv
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import quote_plus




@login_required
def marketplace(request):
    coop_id = request.GET.get("coop")
    coops_qs = Cooperative.objects.order_by("name")
    if coop_id:
        coops_qs = coops_qs.filter(id=coop_id)

    # Secondary availability EXCLUDING buyer’s own listings
    secondary_totals = {
        row["cooperative_id"]: int(row["total"] or 0)
        for row in (
            ShareListing.objects
            .filter(status=ShareListing.Status.ACTIVE)
            .exclude(seller=request.user)
            .values("cooperative_id")
            .annotate(total=Sum("quantity_available"))
        )
    }

    rows = []
    for c in coops_qs:
        primary = int(c.available_primary_shares)
        secondary = secondary_totals.get(c.id, 0)
        rows.append({
            "coop": c,
            "primary": primary,
            "secondary": secondary,                 
            "total_for_buyer": primary + secondary, 
        })

    return render(
        request,
        "shares/marketplace.html",
        {
            "rows": rows,
            "all_coops": Cooperative.objects.order_by("name"),
            "selected_coop_id": coop_id,
        },
    )

@login_required
def buy_listing(request, listing_id: int):
    if request.method != "POST":
        return redirect("shares:marketplace")

    qty = int(request.POST.get("quantity", "0") or "0")
    listing = get_object_or_404(ShareListing, id=listing_id)
    if qty <= 0:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(f"/shares/marketplace/?coop={listing.cooperative_id}")
    
    try:
        buy_from_listing(listing=listing, buyer=request.user, quantity=qty)
        messages.success(request, "Purchase successful.")
    except Exception as e:
        messages.error(request, f"Could not buy shares: {e}")

    return redirect(f"/shares/marketplace/?coop={listing.cooperative_id}")



@login_required
def buy_primary(request):
    if request.method != "POST":
        return redirect("shares:marketplace")

    coop_id = int(request.POST.get("coop_id", "0") or "0")
    qty = int(request.POST.get("quantity", "0") or "0")
    coop = get_object_or_404(Cooperative, id=coop_id)

    if qty <= 0:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(f"/shares/marketplace/?coop={coop.id}")

    try:
        buy_primary_shares_from_coop(coop=coop, buyer=request.user, quantity=qty)
        messages.success(request, "Bought shares from cooperative.")
    except Exception as e:
        messages.error(request, f"Could not buy primary shares: {e}")

    return redirect(f"/shares/marketplace/?coop={coop.id}")



@login_required
def create_listing(request):
    if request.method != "POST":
        return redirect("shares:marketplace")

    coop_id = int(request.POST.get("coop_id", "0") or "0")
    qty = int(request.POST.get("quantity", "0") or "0")

    coop = get_object_or_404(Cooperative, id=coop_id)
    try:
        svc_create_listing(coop=coop, seller=request.user, quantity=qty)
        messages.success(request, "Listing created.")
    except Exception as e:
        messages.error(request, f"Could not create listing: {e}")

    return redirect(f"/shares/marketplace/?coop={coop.id}")



@login_required
def my_listings(request):
    listings = (
        ShareListing.objects.select_related("cooperative")
        .filter(seller=request.user)
        .order_by("-created_at")
    )
    return render(request, "shares/my_listings.html", {"listings": listings})


@login_required
def cancel_listing(request, listing_id: int):
    if request.method != "POST":
        return redirect("shares:my_listings")

    listing = get_object_or_404(ShareListing, id=listing_id, seller=request.user)

    from .services import cancel_listing as svc_cancel_listing
    try:
        svc_cancel_listing(listing=listing, by_user=request.user)
        messages.success(request, "Listing canceled.")
    except Exception as e:
        messages.error(request, f"Could not cancel listing: {e}")

    return redirect("shares:my_listings")


@login_required
def my_trades(request):
    trades_bought = (
        ShareTrade.objects.select_related("cooperative", "seller", "buyer")
        .filter(buyer=request.user)
        .order_by("-created_at")[:50]
    )
    trades_sold = (
        ShareTrade.objects.select_related("cooperative", "seller", "buyer")
        .filter(seller=request.user)
        .order_by("-created_at")[:50]
    )
    return render(
        request,
        "shares/my_trades.html",
        {"trades_bought": trades_bought, "trades_sold": trades_sold},
    )

@login_required
def buy_marketplace(request):
    if request.method != "POST":
        return redirect("shares:marketplace")

    coop_id = int(request.POST.get("coop_id", "0") or "0")
    qty = int(request.POST.get("quantity", "0") or "0")
    source = (request.POST.get("source") or "auto").strip()
    coop = get_object_or_404(Cooperative, id=coop_id)

    if qty <= 0:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(f"/shares/marketplace/?coop={coop.id}")

    try:
        trades = buy_from_marketplace(coop=coop, buyer=request.user, quantity=qty, source=source)
        total = sum(t.total_price for t in trades)
        messages.success(request, f"Purchase successful. Total cost: {total} Tooman.")
    except Exception as e:
        messages.error(request, f"Could not buy shares: {e}")

    return redirect(f"/shares/marketplace/?coop={coop.id}")

@login_required
def shareholder_dashboard(request):
    holdings = (
        ShareHolding.objects.select_related("cooperative")
        .filter(user=request.user)
        .order_by("cooperative__name")
    )

    contributions = (
        Contribution.objects.select_related("project", "project__cooperative")
        .filter(user=request.user)
        .order_by("-created_at")[:20]
    )

    # chart data
    portfolio_labels = [h.cooperative.name for h in holdings if h.quantity > 0]
    portfolio_values = [h.quantity for h in holdings if h.quantity > 0]

    shareholder_profile = getattr(getattr(request.user, "individual", None), "shareholder_profile", None)
    shareholder_id = shareholder_profile.shareholder_id if shareholder_profile else ""
    share_page_url = request.build_absolute_uri(reverse("shares:shareholder_dashboard"))
    share_text = (
        f"My TaavonYar shareholder ID: {shareholder_id}\n"
        f"Use this ID to add me as a board member: {shareholder_id}\n"
        f"Dashboard: {share_page_url}"
    ) if shareholder_id else ""
    qr_image_url = (
        f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={quote_plus(share_text)}"
        if share_text else ""
    )


    return render(
        request,
        "shares/shareholder_dashboard.html",
        {
            "holdings": holdings,
            "contributions": contributions,
            "portfolio_labels_json": portfolio_labels,
            "portfolio_values_json": portfolio_values,
            "shareholder_id": shareholder_id,
            "share_payload": share_text,
            "qr_image_url": qr_image_url,

        },
    )


@login_required
def export_my_holdings_csv(request):
    holdings = (
        ShareHolding.objects.select_related("cooperative")
        .filter(user=request.user)
        .order_by("cooperative__name")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="my_holdings.csv"'
    writer = csv.writer(response)
    writer.writerow(["cooperative", "share_count", "price_per_share", "share_worth_tooman"])

    for h in holdings:
        worth = h.quantity * h.cooperative.price_per_share
        writer.writerow([h.cooperative.name, h.quantity, h.cooperative.price_per_share, worth])

    return response


@login_required
def export_my_contributions_csv(request):
    contributions = (
        Contribution.objects.select_related("project", "project__cooperative")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="my_contributions.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "created_at", "cooperative", "project", "amount_tooman",
        "project_status", "allocated_shares"
    ])

    for c in contributions:
        writer.writerow([
            c.created_at.isoformat(),
            c.project.cooperative.name,
            c.project.title,
            c.amount,
            c.project.status,
            c.allocated_shares if c.allocated_shares is not None else "",
        ])

    return response


@login_required
def export_my_trade_logs_csv(request):
    trades = (
        ShareTrade.objects.select_related("cooperative", "seller__individual", "buyer__individual")
        .filter(models.Q(buyer=request.user) | models.Q(seller=request.user))
        .order_by("-created_at")
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="my_trade_logs.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "created_at", "cooperative", "direction",
        "counterparty", "quantity", "price_per_share", "total_price"
    ])

    for t in trades:
        if t.buyer_id == request.user.id:
            direction = "BUY"
            if t.seller is None:
                counterparty = "COOP_PRIMARY"
            else:
                counterparty = getattr(t.seller.individual, "full_name", t.seller.username)
        else:
            direction = "SELL"
            counterparty = getattr(t.buyer.individual, "full_name", t.buyer.username)

        writer.writerow([
            t.created_at.isoformat(),
            t.cooperative.name,
            direction,
            counterparty,
            t.quantity,
            t.price_per_share,
            t.total_price,
        ])

    return response


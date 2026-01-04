from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib import messages
from coops.models import Cooperative
from projects.models import Contribution
from .models import ShareHolding, ShareListing, ShareTrade
from .services import create_listing as svc_create_listing, buy_from_listing, buy_primary_shares_from_coop


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

    return render(
        request,
        "shares/shareholder_dashboard.html",
        {"holdings": holdings, "contributions": contributions},
    )


@login_required
def marketplace(request):
    coop_id = request.GET.get("coop")
    coops = Cooperative.objects.order_by("name")

    listings = ShareListing.objects.select_related("cooperative", "seller").filter(status=ShareListing.Status.ACTIVE)
    if coop_id:
        listings = listings.filter(cooperative_id=coop_id)

    return render(
        request,
        "shares/marketplace.html",
        {"coops": coops, "listings": listings.order_by("-created_at"), "selected_coop_id": coop_id},
    )


@login_required
def create_listing(request):
    if request.method != "POST":
        return redirect("marketplace")

    
    coop_id = int(request.POST.get("coop_id", "0") or "0")
    qty = int(request.POST.get("quantity", "0") or "0")
    if qty <= 0:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(f"/shares/marketplace/?coop={coop.id}")
    coop = get_object_or_404(Cooperative, id=coop_id)
    try:
        svc_create_listing(coop=coop, seller=request.user, quantity=qty)
    except Exception:
        # keep it simple for now; later we show friendly messages
        pass

    return redirect(f"{'/shares/marketplace/'}?coop={coop.id}")


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
    if qty <= 0:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(f"/shares/marketplace/?coop={coop.id}")


    coop = get_object_or_404(Cooperative, id=coop_id)

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
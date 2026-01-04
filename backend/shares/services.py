from django.db import transaction
from django.db.models import F
from django.db.models import Sum
from django.utils import timezone
from typing import Literal

from coops.models import Cooperative
from .models import ShareHolding, ShareListing, ShareTrade


def _get_holding(coop: Cooperative, user):
    holding, _ = ShareHolding.objects.get_or_create(cooperative=coop, user=user, defaults={"quantity": 0})
    return holding


@transaction.atomic
def create_listing(*, coop: Cooperative, seller, quantity: int) -> ShareListing:
    if quantity <= 0:
        raise ValueError("Quantity must be > 0")

    holding = _get_holding(coop, seller)
    if holding.quantity < quantity:
        raise ValueError("Not enough shares to list")

    # Reserve shares by decreasing seller holding immediately
    holding.quantity = F("quantity") - quantity
    holding.save(update_fields=["quantity"])
    holding.refresh_from_db()

    listing = ShareListing.objects.create(
        cooperative=coop,
        seller=seller,
        quantity_available=quantity,
        price_per_share=coop.price_per_share,  # fixed by cooperative
    )
    return listing


@transaction.atomic
def cancel_listing(*, listing: ShareListing, by_user):
    if listing.seller_id != by_user.id:
        raise PermissionError("Only seller can cancel listing")
    if listing.status != ShareListing.Status.ACTIVE:
        return

    # return remaining shares to seller
    coop = listing.cooperative
    holding = _get_holding(coop, listing.seller)
    holding.quantity = F("quantity") + listing.quantity_available
    holding.save(update_fields=["quantity"])

    listing.status = ShareListing.Status.CANCELED
    listing.save(update_fields=["status"])


@transaction.atomic
def buy_from_listing(*, listing: ShareListing, buyer, quantity: int) -> ShareTrade:
    if quantity <= 0:
        raise ValueError("Quantity must be > 0")
    if listing.status != ShareListing.Status.ACTIVE:
        raise ValueError("Listing is not active")
    if listing.seller_id == buyer.id:
        raise ValueError("You cannot buy your own shares.")
    if quantity > listing.quantity_available:
        raise ValueError("Not enough quantity in listing")

    coop = listing.cooperative

    # Enforce fixed price (buyer can't override)
    price_per_share = coop.price_per_share
    total_price = price_per_share * quantity

    # Give shares to buyer
    buyer_holding = _get_holding(coop, buyer)
    buyer_holding.quantity = F("quantity") + quantity
    buyer_holding.save(update_fields=["quantity"])

    # Reduce listing
    listing.quantity_available = F("quantity_available") - quantity
    listing.save(update_fields=["quantity_available"])
    listing.refresh_from_db()

    if listing.quantity_available == 0:
        listing.status = ShareListing.Status.SOLD_OUT
        listing.save(update_fields=["status"])

    trade = ShareTrade.objects.create(
        cooperative=coop,
        buyer=buyer,
        seller=listing.seller,
        quantity=quantity,
        price_per_share=price_per_share,
        total_price=total_price,
    )
    return trade


@transaction.atomic
def buy_primary_shares_from_coop(*, coop: Cooperative, buyer, quantity: int) -> ShareTrade:
    """
    Buy shares directly from cooperative if it has available_primary_shares.
    Price is always coop.price_per_share.
    Money is abstracted (we just record the trade).
    """
    if quantity <= 0:
        raise ValueError("Quantity must be > 0")

    coop = Cooperative.objects.select_for_update().get(id=coop.id)

    if coop.available_primary_shares < quantity:
        raise ValueError("Cooperative does not have enough shares available for sale")

    # Decrease coop available shares
    coop.available_primary_shares = F("available_primary_shares") - quantity
    coop.save(update_fields=["available_primary_shares"])
    coop.refresh_from_db()

    # Increase buyer holding
    buyer_holding = _get_holding(coop, buyer)
    buyer_holding.quantity = F("quantity") + quantity
    buyer_holding.save(update_fields=["quantity"])

    price_per_share = coop.price_per_share
    total_price = price_per_share * quantity

    trade = ShareTrade.objects.create(
        cooperative=coop,
        buyer=buyer,
        seller=None,  # None means cooperative primary sale
        quantity=quantity,
        price_per_share=price_per_share,
        total_price=total_price,
    )
    return trade


@transaction.atomic
def buy_from_marketplace(*, coop: Cooperative, buyer, quantity: int, source: Literal["primary", "secondary", "auto"] = "auto") -> list[ShareTrade]:
    """
    source:
      - "primary": only buy from coop.available_primary_shares
      - "secondary": only buy from active listings (excluding buyer's own listings)
      - "auto": primary first, then secondary
    Returns list of ShareTrade rows created.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be > 0")
    if source not in ("primary", "secondary", "auto"):
        raise ValueError("Invalid source option")

    trades: list[ShareTrade] = []
    coop = Cooperative.objects.select_for_update().get(id=coop.id)

    price_per_share = coop.price_per_share
    remaining = quantity

    # Compute secondary availability (excluding buyer’s own listings)
    secondary_total = (
        ShareListing.objects
        .filter(cooperative=coop, status=ShareListing.Status.ACTIVE)
        .exclude(seller=buyer)
        .aggregate(total=Sum("quantity_available"))["total"]
        or 0
    )
    secondary_total = int(secondary_total)
    primary_total = int(coop.available_primary_shares)

    if source == "primary" and primary_total < remaining:
        raise ValueError("Not enough primary shares available from cooperative")
    if source == "secondary" and secondary_total < remaining:
        raise ValueError("Not enough secondary shares available from marketplace")
    if source == "auto" and (primary_total + secondary_total) < remaining:
        raise ValueError("Not enough shares available in marketplace")

    def take_primary(amount: int):
        nonlocal remaining
        if amount <= 0:
            return
        coop.available_primary_shares -= amount
        coop.save(update_fields=["available_primary_shares"])

        buyer_holding = _get_holding(coop, buyer)
        buyer_holding.quantity += amount
        buyer_holding.save(update_fields=["quantity"])

        trades.append(
            ShareTrade.objects.create(
                cooperative=coop,
                buyer=buyer,
                seller=None,
                quantity=amount,
                price_per_share=price_per_share,
                total_price=price_per_share * amount,
            )
        )
        remaining -= amount

    def take_secondary(amount: int):
        nonlocal remaining
        if amount <= 0:
            return

        listings = (
            ShareListing.objects
            .select_for_update()
            .filter(cooperative=coop, status=ShareListing.Status.ACTIVE)
            .exclude(seller=buyer)  # prevent buying own shares
            .order_by("created_at", "id")
        )

        for listing in listings:
            if remaining <= 0:
                break
            if listing.quantity_available <= 0:
                continue

            take = min(listing.quantity_available, remaining)
            listing.quantity_available -= take

            if listing.quantity_available == 0:
                listing.status = ShareListing.Status.SOLD_OUT
                listing.save(update_fields=["quantity_available", "status"])
            else:
                listing.save(update_fields=["quantity_available"])

            buyer_holding = _get_holding(coop, buyer)
            buyer_holding.quantity += take
            buyer_holding.save(update_fields=["quantity"])

            trades.append(
                ShareTrade.objects.create(
                    cooperative=coop,
                    buyer=buyer,
                    seller=listing.seller,
                    quantity=take,
                    price_per_share=price_per_share,
                    total_price=price_per_share * take,
                )
            )

            remaining -= take

    # Fulfillment order
    if source == "primary":
        take_primary(remaining)
        return trades

    if source == "secondary":
        take_secondary(remaining)
        if remaining != 0:
            # should not happen due to availability check, but safety:
            raise ValueError("Not enough secondary shares available")
        return trades

    # auto: primary first then secondary
    if remaining > 0 and coop.available_primary_shares > 0:
        take_primary(min(int(coop.available_primary_shares), remaining))

    if remaining > 0:
        take_secondary(remaining)

    if remaining != 0:
        raise ValueError("Not enough shares available")
    return trades
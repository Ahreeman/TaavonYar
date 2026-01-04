import pytest

from shares.services import create_listing, buy_from_listing
from shares.models import ShareHolding, ShareListing
from tests.factories import CooperativeFactory, UserFactory


pytestmark = pytest.mark.django_db


def test_create_listing_reserves_shares_immediately():
    coop = CooperativeFactory(price_per_share=2000)
    seller = UserFactory()

    ShareHolding.objects.create(cooperative=coop, user=seller, quantity=10)

    listing = create_listing(coop=coop, seller=seller, quantity=3)

    holding = ShareHolding.objects.get(cooperative=coop, user=seller)
    assert holding.quantity == 7
    assert listing.quantity_available == 3
    assert listing.price_per_share == 2000


def test_cannot_buy_own_listing():
    coop = CooperativeFactory(price_per_share=1500)
    seller = UserFactory()
    ShareHolding.objects.create(cooperative=coop, user=seller, quantity=10)

    listing = create_listing(coop=coop, seller=seller, quantity=2)

    with pytest.raises(ValueError):
        buy_from_listing(listing=listing, buyer=seller, quantity=1)


def test_buying_from_listing_transfers_shares_to_buyer():
    coop = CooperativeFactory(price_per_share=1000)
    seller = UserFactory()
    buyer = UserFactory()

    ShareHolding.objects.create(cooperative=coop, user=seller, quantity=10)
    listing = create_listing(coop=coop, seller=seller, quantity=4)

    trade = buy_from_listing(listing=listing, buyer=buyer, quantity=3)

    # seller was already reserved on listing creation: 10 -> 6
    seller_h = ShareHolding.objects.get(cooperative=coop, user=seller).quantity
    buyer_h = ShareHolding.objects.get(cooperative=coop, user=buyer).quantity

    assert seller_h == 6
    assert buyer_h == 3

    listing.refresh_from_db()
    assert listing.quantity_available == 1
    assert trade.total_price == 3 * coop.price_per_share
    assert trade.price_per_share == coop.price_per_share

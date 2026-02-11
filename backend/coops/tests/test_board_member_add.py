import pytest

from accounts.models import Individual, Shareholder, BoardMember
from coops.services import add_board_member_by_shareholder_id
from tests.factories import CooperativeFactory, UserFactory


pytestmark = pytest.mark.django_db


def test_add_board_member_by_shareholder_id_creates_member_in_same_coop():
    coop = CooperativeFactory()

    acting_user = UserFactory()
    acting_individual = Individual.objects.create(
        user=acting_user,
        full_name="Acting Board",
        national_number="1111111111",
    )
    BoardMember.objects.create(
        individual=acting_individual,
        cooperative=coop,
        boardmember_id="BM-EXISTING",
        status=BoardMember.AuthorityStatus.ACCEPTED,
    )

    target_user = UserFactory()
    target_individual = Individual.objects.create(
        user=target_user,
        full_name="Target User",
        national_number="2222222222",
    )
    shareholder = Shareholder.objects.create(
        individual=target_individual,
        shareholder_id="SH-TARGET12345",
        bank_account_number="PENDING",
    )

    member = add_board_member_by_shareholder_id(
        acting_user=acting_user,
        shareholder_id=shareholder.shareholder_id,
    )

    assert member.cooperative_id == coop.id
    assert member.individual_id == target_individual.id
    assert member.status == BoardMember.AuthorityStatus.ACCEPTED


def test_add_board_member_by_shareholder_id_rejects_unknown_shareholder_id():
    coop = CooperativeFactory()

    acting_user = UserFactory()
    acting_individual = Individual.objects.create(
        user=acting_user,
        full_name="Acting Board",
        national_number="3333333333",
    )
    BoardMember.objects.create(
        individual=acting_individual,
        cooperative=coop,
        boardmember_id="BM-EXISTING-2",
        status=BoardMember.AuthorityStatus.ACCEPTED,
    )

    with pytest.raises(ValueError):
        add_board_member_by_shareholder_id(
            acting_user=acting_user,
            shareholder_id="SH-NOT-FOUND",
        )

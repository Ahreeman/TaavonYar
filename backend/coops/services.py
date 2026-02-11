import uuid

from accounts.models import BoardMember, Shareholder


def _new_boardmember_id() -> str:
    return f"BM-{uuid.uuid4().hex[:12].upper()}"


def add_board_member_by_shareholder_id(*, acting_user, shareholder_id: str) -> BoardMember:
    """Add a shareholder as an accepted board member in acting board's cooperative."""
    if not hasattr(acting_user, "individual") or not hasattr(acting_user.individual, "board_profile"):
        raise PermissionError("You are not a board member")

    acting_board = acting_user.individual.board_profile
    if acting_board.status != BoardMember.AuthorityStatus.ACCEPTED:
        raise PermissionError("Your board membership is not accepted")

    try:
        shareholder = Shareholder.objects.select_related("individual", "individual__user").get(
            shareholder_id=shareholder_id
        )
    except Shareholder.DoesNotExist as e:
        raise ValueError("No user found for this shareholder ID") from e

    individual = shareholder.individual

    if hasattr(individual, "board_profile"):
        raise ValueError("This user is already a board member")

    return BoardMember.objects.create(
        individual=individual,
        cooperative=acting_board.cooperative,
        boardmember_id=_new_boardmember_id(),
        status=BoardMember.AuthorityStatus.ACCEPTED,
    )

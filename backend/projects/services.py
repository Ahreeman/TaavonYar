from django.db import transaction
from django.db.models import Sum

from .models import Project, Contribution
from shares.models import ShareHolding


@transaction.atomic
def contribute_to_project(*, project: Project, user, amount: int) -> Contribution:
    if project.status != Project.Status.ACTIVE:
        raise ValueError("Project is not active")
    if amount <= 0:
        raise ValueError("Amount must be > 0")

    c = Contribution.objects.create(project=project, user=user, amount=amount)

    # auto update fully funded flag
    total = project.contributions.aggregate(total=Sum("amount"))["total"] or 0
    if total >= project.goal_amount and not project.is_fully_funded:
        project.is_fully_funded = True
        project.save(update_fields=["is_fully_funded"])

    return c


@transaction.atomic
def mark_project_done_and_distribute_shares(*, project: Project) -> None:
    if project.status == Project.Status.DONE:
        return
    if project.status not in (Project.Status.ACTIVE, Project.Status.DRAFT):
        raise ValueError("Project cannot be marked done from this status")

    contributions = list(project.contributions.select_for_update())
    total_contributed = sum(c.amount for c in contributions)

    # Mark done even if no contributions (manual rule), but then nobody gets shares.
    project.status = Project.Status.DONE
    project.save(update_fields=["status"])

    if total_contributed <= 0 or project.shares_to_distribute == 0:
        # set allocated_shares = 0 for traceability if desired
        for c in contributions:
            c.allocated_shares = 0
            c.save(update_fields=["allocated_shares"])
        return

    # Proportional allocation with integer shares.
    # We will distribute remaining rounding shares to biggest contributors first (fair + deterministic).
    raw_allocations = []
    for c in contributions:
        exact = (c.amount / total_contributed) * project.shares_to_distribute
        floor_shares = int(exact)
        remainder = exact - floor_shares
        raw_allocations.append((c, floor_shares, remainder))

    allocated = sum(x[1] for x in raw_allocations)
    remaining = project.shares_to_distribute - allocated

    # sort by remainder desc, then by contribution desc to break ties
    raw_allocations.sort(key=lambda t: (t[2], t[0].amount), reverse=True)

    # give +1 share to top 'remaining' contributors
    for i in range(remaining):
        c, floor_shares, rem = raw_allocations[i]
        raw_allocations[i] = (c, floor_shares + 1, rem)

    # apply allocations: update holdings and record on Contribution
    for c, shares, _ in raw_allocations:
        holding, _ = ShareHolding.objects.get_or_create(
            cooperative=project.cooperative,
            user=c.user,
            defaults={"quantity": 0},
        )
        holding.quantity += shares
        holding.save(update_fields=["quantity"])

        c.allocated_shares = shares
        c.save(update_fields=["allocated_shares"])

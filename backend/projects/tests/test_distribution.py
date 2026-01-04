import pytest

from projects.services import mark_project_done_and_distribute_shares
from projects.models import Project
from shares.models import ShareHolding
from tests.factories import CooperativeFactory, ProjectFactory, UserFactory
from projects.models import Contribution


pytestmark = pytest.mark.django_db


def test_proportional_distribution_rounding_is_fair():
    coop = CooperativeFactory()
    creator = UserFactory()
    project = ProjectFactory(
        cooperative=coop,
        created_by=creator,
        shares_to_distribute=10,
        goal_amount=10_000,
        status=Project.Status.ACTIVE,
    )

    u1 = UserFactory()
    u2 = UserFactory()
    u3 = UserFactory()

    # total = 100
    Contribution.objects.create(project=project, user=u1, amount=50)  # 50%
    Contribution.objects.create(project=project, user=u2, amount=30)  # 30%
    Contribution.objects.create(project=project, user=u3, amount=20)  # 20%

    mark_project_done_and_distribute_shares(project=project)

    project.refresh_from_db()
    assert project.status == Project.Status.DONE

    h1 = ShareHolding.objects.get(cooperative=coop, user=u1).quantity
    h2 = ShareHolding.objects.get(cooperative=coop, user=u2).quantity
    h3 = ShareHolding.objects.get(cooperative=coop, user=u3).quantity

    assert (h1 + h2 + h3) == 10
    # Expected exact proportions: 5,3,2
    assert (h1, h2, h3) == (5, 3, 2)

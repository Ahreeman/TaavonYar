import factory
from django.contrib.auth import get_user_model

from coops.models import Cooperative
from accounts.models import Individual
from projects.models import Project, Contribution
from shares.models import ShareHolding, ShareListing


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "pass12345")


class IndividualFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Individual

    user = factory.SubFactory(UserFactory)
    full_name = factory.Faker("name")
    national_number = factory.Sequence(lambda n: f"NN{100000+n}")
    phone_number = "09120000000"
    address = "Test Address"
    post_id = "1234567890"


class CooperativeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cooperative

    name = factory.Sequence(lambda n: f"Coop{n}")
    village = "Village"
    description = "Desc"
    price_per_share = 1000
    total_shares = 100000
    available_primary_shares = 0


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    cooperative = factory.SubFactory(CooperativeFactory)
    title = factory.Sequence(lambda n: f"Project{n}")
    description = "Project desc"
    goal_amount = 10_000
    shares_to_distribute = 100
    status = Project.Status.ACTIVE
    created_by = factory.SubFactory(UserFactory)


class ContributionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contribution

    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    amount = 1000


class HoldingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareHolding

    cooperative = factory.SubFactory(CooperativeFactory)
    user = factory.SubFactory(UserFactory)
    quantity = 0


class ListingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShareListing

    cooperative = factory.SubFactory(CooperativeFactory)
    seller = factory.SubFactory(UserFactory)
    quantity_available = 1
    status = ShareListing.Status.ACTIVE
    price_per_share = 1000

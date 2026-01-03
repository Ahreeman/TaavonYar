from django.shortcuts import render
from .models import Cooperative

def coop_list(request):
    coops = Cooperative.objects.order_by("name")
    return render(request, "coops/coop_list.html", {"coops": coops})


def coop_detail(request, coop_id: int):
    coop = get_object_or_404(Cooperative, id=coop_id)
    return render(request, "coops/coop_detail.html", {"coop": coop})
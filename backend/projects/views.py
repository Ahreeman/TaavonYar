from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum

from .models import Project
from .services import contribute_to_project


def project_list(request):
    qs = Project.objects.select_related("cooperative").order_by("-created_at")

    coop_id = request.GET.get("coop")
    if coop_id:
        qs = qs.filter(cooperative_id=coop_id)

    return render(request, "projects/project_list.html", {"projects": qs})


def project_detail(request, project_id: int):
    project = get_object_or_404(Project.objects.select_related("cooperative"), id=project_id)
    total = project.contributions.aggregate(total=Sum("amount"))["total"] or 0
    return render(request, "projects/project_detail.html", {"project": project, "total_contributed": total})


@login_required
def contribute(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        amount = int(request.POST.get("amount", "0") or "0")
        contribute_to_project(project=project, user=request.user, amount=amount)
        return redirect("project_detail", project_id=project.id)

    return redirect("project_detail", project_id=project.id)

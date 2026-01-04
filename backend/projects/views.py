from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum

from accounts.models import Individual, BoardMember
from .models import Project
from .services import contribute_to_project, mark_project_done_and_distribute_shares


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


def _require_board_member(user) -> BoardMember:
    if not hasattr(user, "individual"):
        raise PermissionError("User has no Individual profile")

    ind: Individual = user.individual
    if not hasattr(ind, "board_profile"):
        raise PermissionError("User is not a board member")

    board: BoardMember = ind.board_profile
    if board.status != BoardMember.AuthorityStatus.ACCEPTED:
        raise PermissionError("Board member is not accepted by authorities")

    return board


@login_required
def board_dashboard(request):
    try:
        board = _require_board_member(request.user)
    except PermissionError:
        return redirect("accounts:dashboard")

    coop = board.cooperative
    projects = coop.projects.order_by("-created_at")

    return render(request, "projects/board_dashboard.html", {"coop": coop, "projects": projects})


@login_required
def mark_done(request, project_id: int):
    if request.method != "POST":
        return redirect("project_detail", project_id=project_id)

    try:
        board = _require_board_member(request.user)
    except PermissionError:
        return redirect("accounts:dashboard")

    project = get_object_or_404(Project, id=project_id)

    # board member can only mark projects of their own coop
    if project.cooperative_id != board.cooperative_id:
        return redirect("board_dashboard")

    mark_project_done_and_distribute_shares(project=project)
    return redirect("board_dashboard")

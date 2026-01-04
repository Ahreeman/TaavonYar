from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.contrib import messages
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
    return redirect("projects:project_detail", project_id=project.id)


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
        return redirect("projects:project_detail", project_id=project_id)

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


@login_required
def board_project_create(request):
    try:
        board = _require_board_member(request.user)
    except PermissionError:
        messages.error(request, "You are not allowed to create projects.")
        return redirect("accounts:dashboard")

    coop = board.cooperative

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = (request.POST.get("description") or "").strip()
        goal_amount = int(request.POST.get("goal_amount") or "0")
        shares_to_distribute = int(request.POST.get("shares_to_distribute") or "0")
        status = request.POST.get("status") or Project.Status.DRAFT

        if not title:
            messages.error(request, "Title is required.")
            return render(request, "projects/board_project_form.html", {"coop": coop, "project": None, "status_choices": Project.Status.choices})

        if goal_amount <= 0:
            messages.error(request, "Goal amount must be greater than 0.")
            return render(request, "projects/board_project_form.html", {"coop": coop, "project": None, "status_choices": Project.Status.choices})


        if shares_to_distribute <= 0:
            messages.error(request, "Shares to distribute must be greater than 0.")
            return render(request, "projects/board_project_form.html", {"coop": coop, "project": None, "status_choices": Project.Status.choices})


        p = Project.objects.create(
            cooperative=coop,
            title=title,
            description=description,
            goal_amount=goal_amount,
            shares_to_distribute=shares_to_distribute,
            status=status,
            created_by=request.user,
        )

        if "image" in request.FILES:
            p.image = request.FILES["image"]
            p.save(update_fields=["image"])

        messages.success(request, "Project created.")
        return redirect("projects:board_dashboard")

    return render(request, "projects/board_project_form.html", {"coop": coop, "project": None, "status_choices": Project.Status.choices})



@login_required
def board_project_edit(request, project_id: int):
    try:
        board = _require_board_member(request.user)
    except PermissionError:
        messages.error(request, "You are not allowed to edit projects.")
        return redirect("accounts:dashboard")

    project = get_object_or_404(Project, id=project_id)

    if project.cooperative_id != board.cooperative_id:
        messages.error(request, "You can only edit projects of your own cooperative.")
        return redirect("projects:board_dashboard")

    if request.method == "POST":
        project.title = (request.POST.get("title") or "").strip()
        project.description = (request.POST.get("description") or "").strip()
        project.goal_amount = int(request.POST.get("goal_amount") or project.goal_amount)
        project.shares_to_distribute = int(request.POST.get("shares_to_distribute") or project.shares_to_distribute)
        project.status = request.POST.get("status") or project.status

        # recompute fully-funded flag (optional but sensible)
        total = project.total_contributed
        project.is_fully_funded = total >= project.goal_amount

        if "image" in request.FILES:
            project.image = request.FILES["image"]

        project.save()
        messages.success(request, "Project updated.")
        return redirect("projects:board_dashboard")

    return render(request, "projects/board_project_form.html", {"coop": board.cooperative, "project": project, "status_choices": Project.Status.choices})
from django.contrib import admin
from .models import Individual, Shareholder, BoardMember

@admin.register(Individual)
class IndividualAdmin(admin.ModelAdmin):
    list_display = ("full_name", "national_number", "phone_number", "created_at")
    search_fields = ("full_name", "national_number", "phone_number")
    list_filter = ("created_at",)


@admin.register(Shareholder)
class ShareholderAdmin(admin.ModelAdmin):
    list_display = ("shareholder_id", "individual", "bank_account_number", "created_at")
    search_fields = ("shareholder_id", "individual__full_name", "individual__national_number")
    list_filter = ("created_at",)


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ("boardmember_id", "individual", "cooperative", "status", "created_at")
    search_fields = ("boardmember_id", "individual__full_name", "cooperative__name")
    list_filter = ("status", "created_at")
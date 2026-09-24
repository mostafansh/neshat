from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AIExposure, Case, Enrollment, ImageAccess, Presentation, Read, Study, User

admin.site.register(User, UserAdmin)


class ReadOnlyAdmin(admin.ModelAdmin):
    """Records that must never be edited by hand: reads, reveals and the access log."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Study)
class StudyAdmin(ReadOnlyAdmin):
    list_display = ["key", "title", "state", "opened_at"]


@admin.register(Case)
class CaseAdmin(ReadOnlyAdmin):
    list_display = ["study", "position", "code", "slices", "truth", "ai_answer", "ai_confidence", "ai_planted"]
    list_filter = ["study"]


@admin.register(Enrollment)
class EnrollmentAdmin(ReadOnlyAdmin):
    list_display = ["user", "study", "consented_at", "completed_at"]


@admin.register(Presentation)
class PresentationAdmin(ReadOnlyAdmin):
    list_display = ["enrollment", "position", "alias", "shown_at"]


@admin.register(Read)
class ReadAdmin(ReadOnlyAdmin):
    list_display = ["presentation", "stage", "answer", "confidence", "elapsed_ms", "committed_at"]
    list_filter = ["stage"]


@admin.register(AIExposure)
class AIExposureAdmin(ReadOnlyAdmin):
    list_display = ["presentation", "revealed_at"]


@admin.register(ImageAccess)
class ImageAccessAdmin(ReadOnlyAdmin):
    list_display = ["at", "user", "alias", "allowed", "reason", "remote_addr"]
    list_filter = ["allowed"]

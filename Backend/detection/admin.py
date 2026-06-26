from django.contrib import admin

from .models import DetectionResult


@admin.register(DetectionResult)
class DetectionResultAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "label", "score", "is_high_risk", "created_at")
    list_filter = ("label", "is_high_risk", "created_at")
    search_fields = ("label", "reason")

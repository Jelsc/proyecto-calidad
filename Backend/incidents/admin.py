from django.contrib import admin

from .models import Evidence, Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "severity", "status", "created_at")
    list_filter = ("severity", "status", "created_at")
    search_fields = ("title", "summary", "assigned_to")


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "incident", "evidence_type", "collected_at")
    list_filter = ("evidence_type", "collected_at")
    search_fields = ("description", "source_ref")

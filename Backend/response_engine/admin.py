from django.contrib import admin

from .models import ResponseAction


@admin.register(ResponseAction)
class ResponseActionAdmin(admin.ModelAdmin):
    list_display = ("id", "incident", "action_type", "status", "simulated", "executed_at")
    list_filter = ("action_type", "status", "simulated", "executed_at")
    search_fields = ("target_value", "notes")

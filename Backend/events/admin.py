from django.contrib import admin

from .models import TrafficEvent


@admin.register(TrafficEvent)
class TrafficEventAdmin(admin.ModelAdmin):
    list_display = ("id", "source_ip", "destination_ip", "protocol", "destination_port", "created_at")
    list_filter = ("protocol", "created_at")
    search_fields = ("source_ip", "destination_ip", "payload")

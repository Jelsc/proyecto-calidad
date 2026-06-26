from django.db import models


class Report(models.Model):
    title = models.CharField(max_length=128)
    summary = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-generated_at",)

    def __str__(self) -> str:
        return self.title

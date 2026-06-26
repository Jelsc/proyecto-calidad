from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("detection", "0001_initial"),
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Incident",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=128)),
                ("summary", models.TextField(blank=True)),
                (
                    "severity",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
                        default="medium",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("investigating", "Investigating"), ("contained", "Contained"), ("resolved", "Resolved")],
                        default="open",
                        max_length=16,
                    ),
                ),
                ("assigned_to", models.CharField(blank=True, max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "detection",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incidents",
                        to="detection.detectionresult",
                    ),
                ),
                (
                    "source_event",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incidents",
                        to="events.trafficevent",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Evidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("evidence_type", models.CharField(max_length=64)),
                ("description", models.TextField()),
                ("source_ref", models.CharField(blank=True, max_length=128)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("collected_at", models.DateTimeField(auto_now_add=True)),
                (
                    "incident",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence_items", to="incidents.incident"),
                ),
            ],
            options={
                "ordering": ("-collected_at",),
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("incidents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="IncidentTimelineEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("response_policy", "Response Policy"),
                            ("response_action", "Response Action"),
                            ("containment_update", "Containment Update"),
                        ],
                        max_length=64,
                    ),
                ),
                ("message", models.TextField()),
                ("source_ref", models.CharField(blank=True, max_length=128)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "incident",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="timeline_entries", to="incidents.incident"),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]

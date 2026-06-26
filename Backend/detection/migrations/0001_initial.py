from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DetectionResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.FloatField(default=0.0)),
                ("label", models.CharField(max_length=32)),
                ("reason", models.TextField()),
                ("is_high_risk", models.BooleanField(default=False)),
                ("payload_snapshot", models.JSONField(blank=True, default=dict)),
                ("engine_version", models.CharField(default="ml-isoforest-v1", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "event",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="detections",
                        to="events.trafficevent",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
